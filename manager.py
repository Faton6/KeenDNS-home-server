import threading
import subprocess
import schedule
import time
import logging.handlers
import os
import GPUtil
import psutil
import requests
from dotenv import load_dotenv

# Load environment variables from .env (ensure the path is correct)
HOME_PATH=os.path.abspath(os.getcwd())

load_dotenv(HOME_PATH + '.env')
COMPOSE_FILE = os.getenv('COMPOSE_FILE')
if not COMPOSE_FILE:
    COMPOSE_FILE = "docker-compose.yml"
    print("COMPOSE_FILE not set in .env. Using default: docker-compose.yml")

# Telegram settings
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

GPU_LOAD_THRESHOLD = int(os.getenv('GPU_LOAD_THRESHOLD', '50'))
CHECK_INTERVAL = int(os.getenv('CHECK_INTERVAL', '10'))

# Configure logging with rotation
logger = logging.getLogger("DockerManager")
logger.setLevel(logging.INFO)
handler = logging.handlers.RotatingFileHandler(HOME_PATH + "manager.log", maxBytes=5*1024*1024, backupCount=3)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

def send_telegram(msg):
    if TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
        try:
            requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
                data={'chat_id': TELEGRAM_CHAT_ID, 'text': msg}
            )
        except Exception as e:
            logger.error(f"Telegram send error: {e}")

def run_compose(cmd):
    full_cmd = f'docker-compose -f "{COMPOSE_FILE}" {cmd}'
    try:
        subprocess.check_call(full_cmd, shell=True)
        logger.info(f"Compose command '{cmd}' executed successfully.")
    except subprocess.CalledProcessError as e:
        logger.error(f"Error executing '{cmd}': {e}")
        send_telegram(f"Error executing docker-compose command: {cmd}\n{e}")

def docker_available():
    try:
        subprocess.check_output("docker ps", shell=True)
        return True
    except Exception as e:
        logger.error("Docker is unavailable: " + str(e))
        send_telegram("Docker is unavailable! Make sure Docker Desktop is running.")
        return False

def containers_up():
    if docker_available():
        run_compose("up -d")
    else:
        logger.warning("Containers not starting because Docker is unavailable.")

def containers_stop(service=None):
    if docker_available():
        if service:
            run_compose(f"stop {service}")
        else:
            run_compose("stop")
    else:
        logger.warning("Unable to stop containers because Docker is unavailable.")

def containers_start(service=None):
    if docker_available():
        if service:
            run_compose(f"start {service}")
        else:
            run_compose("start")
    else:
        logger.warning("Unable to start containers because Docker is unavailable.")

def containers_pause():
    if docker_available():
        run_compose("pause")
    else:
        logger.warning("Unable to pause containers because Docker is unavailable.")

def containers_unpause():
    if docker_available():
        run_compose("unpause")
    else:
        logger.warning("Unable to unpause containers because Docker is unavailable.")

def safe_container_update():
    logger.info("Checking for container updates...")
    if docker_available():
        run_compose("pull")
        run_compose("up -d --remove-orphans")
        logger.info("Containers updated successfully.")
        send_telegram("Containers updated successfully.")
    else:
        logger.warning("Container update failed because Docker is unavailable.")

def make_backup(service=None):
    logger.info("Starting backup...")
    services = [service] if service else []
    if not services:
        for key in os.environ:
            if key.startswith("BACKUP_") and key.endswith("_SRC"):
                svc = key[7:-4]
                services.append(svc.lower())
    for svc in services:
        src = os.getenv("BACKUP_" + svc.upper() + "_SRC")
        dst = os.getenv("BACKUP_" + svc.upper() + "_DST")
        if src and dst:
            os.makedirs(dst, exist_ok=True)
            logger.info(f"Backing up {svc}: {src} -> {dst}")
            subprocess.run(f'robocopy "{src}" "{dst}" /E /XO', shell=True)
        else:
            logger.info(f"No backup configuration found for {svc}.")
    logger.info("Backup completed.")

def health_check(service=None):
    services = [service] if service else []
    if not services:
        for key in os.environ:
            if key.startswith("HEALTH_") and key.endswith("_URL"):
                svc = key[7:-4]
                services.append(svc.lower())
    results = {}
    for svc in services:
        url = os.getenv("HEALTH_" + svc.upper() + "_URL")
        if url:
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    results[svc] = "Healthy"
                else:
                    results[svc] = f"Unhealthy (status code {response.status_code})"
            except Exception as e:
                results[svc] = f"Error: {e}"
        else:
            results[svc] = "Health check not configured."
    return results

def is_service_running(service):
    try:
        output = subprocess.check_output(
            f'docker-compose -f "{COMPOSE_FILE}" ps {service}', 
            shell=True, 
            universal_newlines=True
        )
        return "Up" in output
    except Exception as e:
        logger.error(f"Error checking status for {service}: {e}")
        return False

def status_all():
    try:
        output = subprocess.check_output(
            f'docker-compose -f "{COMPOSE_FILE}" config --services', 
            shell=True, 
            universal_newlines=True
        )
        services = output.strip().splitlines()
    except Exception as e:
        logger.error("Error fetching service list: " + str(e))
        services = []
    statuses = {}
    for svc in services:
        statuses[svc] = "Running" if is_service_running(svc) else "Stopped"
    return statuses

def gpu_under_load():
    try:
        gpus = GPUtil.getGPUs()
        return any(gpu.load * 100 >= GPU_LOAD_THRESHOLD for gpu in gpus)
    except Exception as e:
        logger.error("Error checking GPU load: " + str(e))
        return False

def manage_resources():
    if gpu_under_load():
        logger.info("High GPU load detected, pausing containers.")
        containers_pause()
        send_telegram("Containers paused (high GPU load detected).")
        while gpu_under_load():
            time.sleep(CHECK_INTERVAL)
        containers_unpause()
        logger.info("GPU load normalized, containers resumed.")
        send_telegram("Containers resumed after GPU load normalized.")

# ======= Telegram Bot (python-telegram-bot v20) =======
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "Hello!\nAvailable commands:\n"
        "/help – Show this help message\n"
        "/backup [service] – Start backup for a service (or all if omitted)\n"
        "/stop [service] – Stop a service (or all if omitted)\n"
        "/startservice [service] – Start a service (or all if omitted)\n"
        "/status [service] – Get service status\n"
        "/health [service] – Run health check for a service\n"
        "/update – Update containers\n"
    )
    await update.message.reply_text(text)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start_command(update, context)

async def backup_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if args:
        svc = args[0]
        make_backup(svc)
        await update.message.reply_text(f"Backup for service {svc} started.")
    else:
        make_backup()
        await update.message.reply_text("Backup for all services started.")

async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if args:
        svc = args[0]
        containers_stop(svc)
        await update.message.reply_text(f"Service {svc} stopped.")
    else:
        containers_stop()
        await update.message.reply_text("All services stopped.")

async def start_service_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if args:
        svc = args[0]
        containers_start(svc)
        await update.message.reply_text(f"Service {svc} started.")
    else:
        containers_start()
        await update.message.reply_text("All services started.")

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if args:
        svc = args[0]
        status = "Running" if is_service_running(svc) else "Stopped"
        await update.message.reply_text(f"Service {svc}: {status}.")
    else:
        statuses = status_all()
        msg = "\n".join(f"{svc}: {status}" for svc, status in statuses.items())
        await update.message.reply_text(msg)

async def health_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if args:
        svc = args[0]
        results = health_check(svc)
        msg = "\n".join(f"{s}: {r}" for s, r in results.items())
        await update.message.reply_text(msg)
    else:
        results = health_check()
        msg = "\n".join(f"{s}: {r}" for s, r in results.items())
        await update.message.reply_text(msg)

async def update_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    safe_container_update()
    await update.message.reply_text("Container update initiated.")

def bot_thread():
    # Launch the bot synchronously in a separate thread.
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("backup", backup_command))
    application.add_handler(CommandHandler("stop", stop_command))
    application.add_handler(CommandHandler("startservice", start_service_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("health", health_command))
    application.add_handler(CommandHandler("update", update_command))
    application.run_polling()

def start_bot():
    thread = threading.Thread(target=bot_thread)
    thread.daemon = True
    thread.start()

def schedule_tasks():
    schedule.every().day.at("03:00").do(make_backup)
    schedule.every().day.at("04:00").do(safe_container_update)
    schedule.every(1).minutes.do(manage_resources)

def main():
    logger.info("DockerManager started")
    send_telegram("DockerManager started.")
    containers_up()
    start_bot()
    schedule_tasks()
    while True:
        schedule.run_pending()
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
