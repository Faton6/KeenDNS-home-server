# Доступная из интернета инфраструктура с Immich и Nextcloud

**Для английской версии документации смотрите [English Documentation](README.md).**

Данная документация описывает, как настроить автоматизированную инфраструктуру на Windows с использованием Docker Desktop (с WSL2). В составе системы:

- **Immich** – для хранения фотографий.
- **Nextcloud** – для хранения документов.
- **Portainer** – для управления контейнерами.
- Автоматизирующий скрипт (`manager.py`), который:
  - Поднимает, останавливает и обновляет контейнеры.
  - Выполняет резервное копирование.
  - Отслеживает нагрузку на ресурсы.
  - Предоставляет возможность управления через Telegram-бота.

> **Примечание:**  
> Убедитесь, что Docker Desktop установлен с поддержкой WSL2 и что выбранные диски (например, D:) доступны (расшарены) в настройках Docker Desktop.

---

## Содержание

- [Структура каталогов](#структура-каталогов)
- [Конфигурационные файлы](#конфигурационные-файлы)
  - [.env файл](#env-файл)
  - [docker-compose.yml](#docker-composeyml)
  - [manager.py](#managerpy)
- [Установка и настройка](#установка-и-настройка)
- [Создание Telegram-бота](#создание-telegram-бота)
- [Запуск инфраструктуры](#запуск-инфраструктуры)
- [Команды Telegram-бота](#команды-telegram-бота)
- [Устранение неполадок](#устранение-неполадок)
- [Дополнительные рекомендации](#дополнительные-рекомендации)

---

## Структура каталогов

Создайте каталог, например, `D:\home_service\`, и поместите в него файлы из репозитория:
- [.env](.env)
- [docker-compose.yml](docker-compose.yml)
- [manager.py](manager.py)

Установка и настройка
Установите Docker Desktop:

Убедитесь, что установлен Docker Desktop с поддержкой WSL2.

В настройках Docker Desktop расшарьте диск (например, D:).

Настройте файл .env:

Отредактируйте D:\home_service\.env по своим требованиям.

Важно: используйте Windows-пути, например, UPLOAD_LOCATION=D:\home_service\immich\immich-data.

Установите зависимости Python:
Откройте CMD или PowerShell и выполните:

bash
Copy
pip install schedule psutil GPUtil python-dotenv requests python-telegram-bot
Разверните контейнеры:
Выполните в CMD или WSL:

bash
Copy
docker-compose -f D:\home_service\docker-compose.yml up -d
Проверьте, что контейнеры работают:

bash
Copy
docker ps
Доступ к сервисам:

Immich: http://localhost:2283

Nextcloud: http://localhost:8081

Portainer: http://localhost:9000

Запустите скрипт manager.py:
Выполните:

bash
Copy
python D:\home_service\manager.py
Скрипт:

Поднимет контейнеры (если Docker доступен),

Запустит Telegram-бота,

Запланирует автоматические задачи (резервное копирование, обновление, мониторинг загрузки).

(Опционально) Автозапуск manager.py:
Чтобы запускать manager.py при старте системы, создайте задачу в Планировщике задач Windows. Откройте PowerShell с правами администратора и выполните:

powershell
Copy
$Action = New-ScheduledTaskAction -Execute 'python.exe' -Argument 'D:\home_service\manager.py'
$Trigger = New-ScheduledTaskTrigger -AtLogOn
$Principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -RunLevel Highest
Register-ScheduledTask -Action $Action -Trigger $Trigger -Principal $Principal -TaskName "DockerInfraManager" -Description "Автоматическое управление Docker инфраструктурой"
Создание Telegram-бота
Создание бота:

Откройте Telegram и найдите официального @BotFather.

Отправьте команду /newbot и следуйте инструкциям, чтобы создать нового бота (имя и username бота, username должен заканчиваться на "bot", например, MyDockerBot).

После создания BotFather предоставит вам bot token (например, 123456789:ABCDefGhIJKlmnoPQRSTuvWXyz).

Получите ваш Chat ID:

Начните чат с вашим ботом.

Используйте сервис, например, @userinfobot, чтобы узнать свой Telegram Chat ID.

Обновите соответствующие переменные в файле .env:

ini
Copy
TELEGRAM_TOKEN=YOUR_TELEGRAM_BOT_TOKEN
TELEGRAM_CHAT_ID=YOUR_TELEGRAM_CHAT_ID
Запуск инфраструктуры
Разверните контейнеры:

bash
Copy
docker-compose -f D:\home_service\docker-compose.yml up -d
Запустите manager.py:

bash
Copy
python D:\home_service\manager.py
Доступ к сервисам:

Immich: http://localhost:2283

Nextcloud: http://localhost:8081

Portainer: http://localhost:9000

Команды Telegram-бота
Когда manager.py запущен, вы можете управлять инфраструктурой через Telegram, отправляя вашему боту следующие команды:

/help – Показать справку с описанием доступных команд.

/backup [service] – Запустить резервное копирование указанного сервиса (если не указан, для всех).

/stop [service] – Остановить указанный сервис (если не указан, остановить все).

/startservice [service] – Запустить указанный сервис (если не указан, запустить все).

/status [service] – Получить статус (Running/Stopped) указанного сервиса (если не указан, для всех).

/health [service] – Выполнить проверку работоспособности указанного сервиса (если не указан, для всех).

/update – Обновить контейнеры (подтянув последние образы и перезапустив их).

Устранение неполадок
Тома не монтируются/файлы не появляются:
Проверьте, что в файле .env используются Windows-пути (например, UPLOAD_LOCATION=D:\home_service\immich\immich-data) и что диск D: добавлен в File Sharing в настройках Docker Desktop.

Проблемы с подключением к Docker:
Убедитесь, что Docker Desktop запущен.

Проблемы с Telegram-ботом:
Проверьте правильность указанных в .env переменных TELEGRAM_TOKEN и TELEGRAM_CHAT_ID и наличие интернет-соединения.

Дополнительные рекомендации
Регулярное резервное копирование:
Скрипт настроен на ежедневное резервное копирование. При необходимости измените расписание в manager.py.

Мониторинг ресурсов:
Скрипт приостанавливает работу контейнеров при высокой загрузке GPU (например, во время игр) и автоматически их возобновляет.

Контроль версий:
Рекомендуется использовать систему контроля версий (например, Git) для управления конфигурационными файлами.

Расширяемость:
Для добавления новых сервисов обновите docker-compose.yml и добавьте соответствующие переменные резервного копирования и проверки работоспособности в .env.

