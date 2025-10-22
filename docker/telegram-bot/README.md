# 🤖 Telegram Bot для мониторинга Bitrix CDN

Умный Telegram бот для мониторинга и управления системой Bitrix CDN с интеграцией AI.

## 🚀 Возможности

### 📊 Мониторинг
- **Статус сервисов**: Nginx, Redis, WebP конвертер, Prometheus
- **Health checks**: автоматические проверки всех компонентов
- **Метрики**: производительность в реальном времени
- **Контейнеры**: статус всех Docker контейнеров

### 🤖 AI-анализ
- **GPT интеграция**: анализ состояния системы
- **Рекомендации**: оптимизация производительности
- **Тренды**: прогнозирование проблем
- **Естественный язык**: общение с системой

### 🔔 Уведомления
- **Проактивные**: автоматические уведомления о проблемах
- **Критические алерты**: мгновенные оповещения
- **Настраиваемые**: подписка/отписка пользователей
- **Многоуровневые**: критические, предупреждения, информационные

## 📋 Команды бота

### Основные команды
- `/start` - Приветствие и список команд
- `/help` - Полный список команд
- `/status` - Общий статус системы
- `/report` - Полный отчет о системе

### Мониторинг сервисов
- `/nginx` - Детальная информация о Nginx
- `/redis` - Статистика Redis
- `/webp` - Статус WebP конвертера
- `/prometheus` - Метрики Prometheus
- `/containers` - Список всех контейнеров
- `/health` - Health checks всех сервисов

### Анализ и диагностика
- `/analyze` - AI-анализ состояния системы
- `/cache` - Статистика кеширования
- `/alerts` - Текущие алерты
- `/logs [service]` - Логи сервиса
- `/metrics [service]` - Метрики сервиса

### Управление
- `/restart [service]` - Перезапуск сервиса
- `/subscribe` - Подписка на уведомления
- `/unsubscribe` - Отписка от уведомлений

## 🛠️ Установка и настройка

### 1. Создание Telegram бота
1. Напишите @BotFather в Telegram
2. Создайте нового бота командой `/newbot`
3. Получите токен бота
4. Добавьте токен в переменную `TELEGRAM_BOT_TOKEN`

### 2. Настройка OpenAI
1. Получите API ключ на https://platform.openai.com/
2. Добавьте ключ в переменную `OPENAI_API_KEY`

### 3. Запуск бота
```bash
# Сборка образа
./docker-manage.sh telegram-bot build

# Запуск бота
./docker-manage.sh telegram-bot start

# Просмотр логов
./docker-manage.sh telegram-bot logs

# Статус бота
./docker-manage.sh telegram-bot status
```

## ⚙️ Конфигурация

### Переменные окружения
```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
OPENAI_API_KEY=your_openai_api_key_here
REDIS_PASSWORD=bitrix_cdn_secure_2024
```

### Настройка доступа
В файле `config.yml` можно ограничить доступ:
```yaml
telegram:
  allowed_users: [123456789, 987654321]  # Список chat_id
```

## 🔧 Архитектура

### Компоненты
- **main.py**: точка входа, регистрация команд
- **handlers.py**: обработчики команд Telegram
- **prometheus_client.py**: клиент для Prometheus API
- **docker_client.py**: клиент для Docker API
- **ai_analyzer.py**: AI-анализ с GPT
- **notifications.py**: служба уведомлений
- **alerts.py**: интеграция с AlertManager

### Интеграции
- **Prometheus**: метрики и алерты
- **Docker API**: статус контейнеров
- **AlertManager**: управление алертами
- **OpenAI GPT**: AI-анализ
- **Redis**: кеширование данных

## 📈 Мониторинг

### Метрики
- **Nginx**: запросы, соединения, кеш
- **Redis**: память, ключи, hit rate
- **WebP**: конвертированные файлы, очередь
- **Система**: CPU, память, диск, сеть

### Алерты
- **Критические**: остановка сервисов
- **Предупреждения**: высокая нагрузка
- **Информационные**: статистика

## 🔒 Безопасность

### Ограничения доступа
- **Список пользователей**: только разрешенные chat_id
- **Rate limiting**: ограничение частоты команд
- **Логирование**: все действия записываются

### Привилегии
- **Read-only**: бот не может изменять систему
- **Docker socket**: доступ только для чтения
- **Network**: изолированная сеть

## 🚀 Разработка

### Структура проекта
```
docker/telegram-bot/
├── Dockerfile
├── requirements.txt
├── config.yml
├── bot/
│   ├── __init__.py
│   ├── main.py
│   ├── handlers.py
│   ├── prometheus_client.py
│   ├── docker_client.py
│   ├── ai_analyzer.py
│   ├── notifications.py
│   ├── alerts.py
│   └── utils.py
└── README.md
```

### Добавление новых команд
1. Добавьте обработчик в `handlers.py`
2. Зарегистрируйте команду в `main.py`
3. Обновите документацию

### Тестирование
```bash
# Локальное тестирование
python -m bot.main

# Тестирование в Docker
docker compose up telegram-bot
```

## 📞 Поддержка

При возникновении проблем:
1. Проверьте логи: `./docker-manage.sh telegram-bot logs`
2. Проверьте статус: `./docker-manage.sh telegram-bot status`
3. Перезапустите бота: `./docker-manage.sh telegram-bot restart`

## 📝 Лицензия

MIT License - см. файл LICENSE в корне проекта.

---

**Автор**: Chibilyaev Alexandr <info@aachibilyaev.com>  
**Компания**: AAChibilyaev LTD  
**Версия**: 1.0.0
