# Internet access home Infrastructure with Immich and Nextcloud

**For the Russian version of this documentation, see [Russian](READMERU.md).**

This document describes how to set up an automated Docker-based infrastructure on a Windows PC using Docker Desktop (with WSL2). The system includes:

- **Immich** for photo storage.
- **Nextcloud** for document storage.
- **Portainer** for container management.
- An automated management script (`manager.py`) that:
  - Starts/stops/updates containers.
  - Performs backups.
  - Monitors resource usage.
  - Provides interactive control via a Telegram bot.

> **Note:**  
> Make sure Docker Desktop is installed with WSL2 enabled and that your Windows drive(s) (e.g., D:) are shared in Docker Desktop settings.

---

## Table of Contents

- [Directory Structure](#directory-structure)
- [Configuration Files](#configuration-files)
  - [.env File](#env-file)
  - [docker-compose.yml](#docker-composeyml)
  - [manager.py](#managerpy)
- [Installation and Setup](#installation-and-setup)
- [Creating Your Telegram Bot](#creating-your-telegram-bot)
- [Running the Infrastructure](#running-the-infrastructure)
- [Telegram Bot Commands](#telegram-bot-commands)
- [Troubleshooting](#troubleshooting)
- [Additional Recommendations](#additional-recommendations)

---

## Directory Structure

Create a directory (e.g., `D:\home_service\`) with the following files from repository:
- [.env](.env)
- [docker-compose.yml](docker-compose.yml)
- [manager.py](manager.py)

Installation and Setup
Install Docker Desktop:

Ensure Docker Desktop (with WSL2 integration) is installed.

In Docker Desktop settings, share the drive(s) you plan to use (e.g., D:).

Create the Directory Structure:

Create D:\home_service\ and place .env, docker-compose.yml, and manager.py inside.

Configure the .env File:

Edit D:\home_service\.env as needed.

Important: Use Windows paths (e.g., UPLOAD_LOCATION=D:\home_service\immich\immich-data).

Install Python Dependencies:
Open CMD or PowerShell and run:

bash
Copy
pip install schedule psutil GPUtil python-dotenv requests python-telegram-bot
Deploy the Containers:
In CMD or WSL, execute:

bash
Copy
docker-compose -f D:\home_service\docker-compose.yml up -d
Verify containers are running with:

bash
Copy
docker ps
Access services:

Immich: http://localhost:2283

Nextcloud: http://localhost:8081

Portainer: http://localhost:9000

Run the Manager Script:
In CMD or PowerShell, execute:

bash
Copy
python D:\home_service\manager.py
This script will start the containers (if Docker is available), launch the Telegram bot, and schedule automated tasks (backups, updates, resource monitoring).

(Optional) Set Up Autostart for manager.py:
To run manager.py at system startup, create a scheduled task. Open PowerShell as Administrator and run:

powershell
Copy
$Action = New-ScheduledTaskAction -Execute 'python.exe' -Argument 'D:\home_service\manager.py'
$Trigger = New-ScheduledTaskTrigger -AtLogOn
$Principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -RunLevel Highest
Register-ScheduledTask -Action $Action -Trigger $Trigger -Principal $Principal -TaskName "DockerInfraManager" -Description "Automated Docker Infrastructure Manager"
Creating Your Telegram Bot
Create a Bot:

Open Telegram and search for the official @BotFather.

Start a chat with BotFather and send the command /newbot.

Follow the instructions to name your bot and choose a username (must end with "bot", e.g., MyDockerBot).

BotFather will provide you with a bot token (e.g., 123456789:ABCDefGhIJKlmnoPQRSTuvWXyz).

Get Your Chat ID:

Start a chat with your new bot.

Visit @userinfobot or use another method to obtain your Telegram chat ID.

Update your .env file with the token and chat ID:

ini
Copy
TELEGRAM_TOKEN=YOUR_TELEGRAM_BOT_TOKEN
TELEGRAM_CHAT_ID=YOUR_TELEGRAM_CHAT_ID
Running the Infrastructure
Deploy Containers:

bash
Copy
docker-compose -f D:\home_service\docker-compose.yml up -d
Run the Manager Script:

bash
Copy
python D:\home_service\manager.py
Access Services:

Immich: http://localhost:2283

Nextcloud: http://localhost:8081

Portainer: http://localhost:9000

Telegram Bot Commands
While manager.py is running, interact with your Telegram bot using these commands:

/help – Display this help message.

/backup [service] – Trigger a backup for a specified service (or all services if omitted).

/stop [service] – Stop a specified service (or all services if omitted).

/startservice [service] – Start a specified service (or all services if omitted).

/status [service] – Get the status (Running/Stopped) of a specified service (or all services if omitted).

/health [service] – Perform a health check on a specified service (or all services if omitted).

/update – Update containers by pulling the latest images and restarting them.

Troubleshooting
Volume Issues:
Ensure your .env file uses Windows paths (e.g., UPLOAD_LOCATION=D:\home_service\immich\immich-data) and that the drive is shared in Docker Desktop.

Docker Connection Errors:
Confirm that Docker Desktop is running.

Telegram Bot Issues:
Verify that your bot token and chat ID are correctly set in the .env file and that you have network connectivity.

Additional Recommendations
Regular Backups:
The script schedules daily backups. Adjust the schedule in manager.py if needed.

Resource Monitoring:
The script pauses containers during high GPU load (e.g., when gaming) and resumes them afterward.

Version Control:
Use Git or another version control system to manage your configuration files.

Expandability:
To add new services, update docker-compose.yml and add corresponding backup and health-check variables in .env.
