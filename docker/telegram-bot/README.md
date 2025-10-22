# Telegram Bot для мониторинга Bitrix CDN

Интеллектуальный бот для мониторинга и управления инфраструктурой Bitrix CDN с AI-анализом на базе GPT-4o.

## Описание проекта

Этот Telegram бот предоставляет комплексный мониторинг и управление всеми сервисами Bitrix CDN:
- **NGINX** - основной веб-сервер с обработкой изображений
- **WebP Converter** - асинхронная конвертация изображений в WebP/AVIF
- **Redis** - кеширование метаданных
- **SSHFS** - монтирование файлов с сервера Bitrix
- **Prometheus** - сбор метрик со всех сервисов
- **Grafana** - визуализация метрик и дашборды
- **AlertManager** - управление алертами
- **Node Exporter** - системные метрики хоста
- **Nginx/Redis Exporters** - метрики сервисов

## Возможности бота

### 🔍 Мониторинг сервисов
- `/status` - Общий статус всех контейнеров
- `/containers` - Детальный список всех сервисов
- `/health` - Health checks всех сервисов
- `/nginx` - Статистика Nginx (connections, requests, cache)
- `/redis` - Метрики Redis (memory, keys, hit rate)
- `/webp` - Статус WebP конвертера (queue, processed files)
- `/cache` - Статистика кеширования Nginx и Redis

### 🤖 AI-анализ с GPT-4o
- `/analyze` - Комплексный AI-анализ состояния системы
- `/ask [вопрос]` - Задать вопрос боту о системе
- `/trends` - Анализ трендов производительности
- `/suggest` - Рекомендации по оптимизации от AI
- `/debug` - Детальная диагностика проблем

### 📊 Отчеты и алерты
- `/report` - Полный отчет о системе
- `/alerts` - Активные алерты из AlertManager
- `/quick` - Быстрый обзор ключевых метрик
- `/summary` - Сводка за последний час

### 🔔 Проактивные уведомления
- `/subscribe` - Подписка на автоматические уведомления
- `/unsubscribe` - Отписка от уведомлений
- Автоматические алерты при критических проблемах
- Уведомления о падении контейнеров
- Алерты по метрикам производительности

### ℹ️ Помощь и подсказки
- `/help` - Список всех команд
- `/commands` - Интерактивная подсказка команд
- `/tips` - Полезные советы по использованию

## Архитектура

### Мониторируемые сервисы

```
┌─────────────────────────────────────────────────────────────┐
│                     Bitrix CDN Infrastructure                │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  NGINX   │  │  Redis   │  │  WebP    │  │  SSHFS   │   │
│  │ (80/443) │  │ (6379)   │  │ (8088)   │  │  mount   │   │
│  └─────┬────┘  └─────┬────┘  └─────┬────┘  └──────────┘   │
│        │             │             │                         │
│        └─────────────┴─────────────┘                         │
│                      │                                        │
│            ┌─────────▼─────────┐                            │
│            │   Prometheus      │◄──── Exporters             │
│            │     (9090)        │      (nginx, redis, node)  │
│            └─────────┬─────────┘                            │
│                      │                                        │
│         ┌────────────┴────────────┐                         │
│         │                         │                          │
│    ┌────▼────┐             ┌─────▼──────┐                  │
│    │ Grafana │             │AlertManager│                   │
│    │ (3000)  │             │   (9093)   │                   │
│    └─────────┘             └─────┬──────┘                   │
│                                   │                          │
│                          ┌────────▼────────┐                │
│                          │ Telegram Bot    │                │
│                          │  + GPT-4o AI    │                │
│                          └─────────────────┘                │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### Компоненты бота

```
telegram-bot/
├── bot/
│   ├── main.py              # Точка входа
│   ├── handlers.py          # Обработчики команд (1400+ строк)
│   ├── ai_analyzer.py       # AI-анализ с GPT-4o
│   ├── docker_client.py     # Взаимодействие с Docker API
│   ├── prometheus_client.py # Получение метрик из Prometheus
│   ├── alerts.py            # Работа с AlertManager
│   ├── notifications.py     # Проактивные уведомления
│   ├── models.py            # Модели данных (Pydantic)
│   ├── config_loader.py     # Загрузка конфигурации
│   └── utils.py             # Утилиты
├── config.yml               # Конфигурация бота
├── requirements.txt         # Зависимости
├── Dockerfile              # Docker образ
└── README.md               # Эта документация
```

## Установка и настройка

### 1. Переменные окружения

Создайте файл `.env` в корне проекта:

```bash
# Telegram Bot
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here

# OpenAI API (для AI-анализа)
OPENAI_API_KEY=your_openai_api_key_here

# Redis (используется ботом)
REDIS_PASSWORD=bitrix_cdn_secure_2024

# Для Netdata (опционально)
NETDATA_CLAIM_TOKEN=your_netdata_token
NETDATA_CLAIM_ROOMS=your_room_id
```

### 2. Получение Telegram Bot Token

1. Напишите [@BotFather](https://t.me/BotFather) в Telegram
2. Отправьте `/newbot`
3. Следуйте инструкциям и получите токен
4. Добавьте токен в `.env`

### 3. Получение OpenAI API Key

1. Зарегистрируйтесь на [platform.openai.com](https://platform.openai.com/)
2. Создайте API key в разделе API Keys
3. Добавьте ключ в `.env`
4. Убедитесь, что у вас есть доступ к GPT-4o

### 4. Конфигурация бота

Отредактируйте `docker/telegram-bot/config.yml`:

```yaml
telegram:
  token: "${TELEGRAM_BOT_TOKEN}"
  allowed_users: [142636541]  # Ваш Telegram user ID
  allowed_groups: []           # ID разрешенных групп
  admin_users: [142636541]     # Администраторы

prometheus:
  url: "http://prometheus:9090"

docker:
  socket: "/var/run/docker.sock"

openai:
  api_key: "${OPENAI_API_KEY}"
  model: "gpt-4o"  # Используется GPT-4o

alertmanager:
  url: "http://alertmanager:9093"

notifications:
  enabled: true
  check_interval: 60  # Проверка каждые 60 секунд
  critical_only: false

services:
  - name: nginx
    container: cdn-nginx
  - name: redis
    container: cdn-redis
  - name: webp-converter
    container: cdn-webp-converter-async
  - name: sshfs
    container: cdn-sshfs
  - name: prometheus
    container: cdn-prometheus
  - name: grafana
    container: cdn-grafana
  - name: alertmanager
    container: cdn-alertmanager
  - name: node-exporter
    container: cdn-node-exporter
  - name: nginx-exporter
    container: cdn-nginx-exporter
  - name: redis-exporter
    container: cdn-redis-exporter
```

### 5. Узнать свой Telegram User ID

Отправьте любое сообщение боту [@userinfobot](https://t.me/userinfobot) и скопируйте ваш ID.

### 6. Сборка и запуск

```bash
# Сборка бота
docker compose build telegram-bot

# Запуск бота
docker compose up -d telegram-bot

# Проверка логов
docker compose logs -f telegram-bot
```

## Использование

### Первый запуск

1. Найдите вашего бота в Telegram по username
2. Отправьте `/start`
3. Бот проверит авторизацию (по User ID из config.yml)
4. Используйте `/commands` для списка доступных команд

### Основные команды

```
/start       - Запуск бота и приветствие
/help        - Полный список команд
/commands    - Интерактивная подсказка

🔍 Мониторинг:
/status      - Статус всех сервисов
/containers  - Список контейнеров
/health      - Health checks
/nginx       - Метрики Nginx
/redis       - Статистика Redis
/webp        - WebP конвертер
/cache       - Статистика кеша

🤖 AI-Анализ:
/analyze     - Анализ системы с GPT-4o
/ask         - Задать вопрос боту
/trends      - Анализ трендов
/suggest     - Рекомендации

📊 Отчеты:
/report      - Полный отчет
/alerts      - Активные алерты
/quick       - Быстрый обзор

🔔 Уведомления:
/subscribe   - Подписка
/unsubscribe - Отписка
```

### Примеры использования

**Проверка статуса системы:**
```
/status
```
Получите краткий обзор всех сервисов: какие работают, какие остановлены.

**AI-анализ проблем:**
```
/analyze
```
Бот соберет все метрики, проанализирует их с помощью GPT-4o и предоставит:
- Общий статус (healthy/warning/critical)
- Оценку здоровья системы (0-100)
- Обнаруженные проблемы
- Рекомендации по устранению
- Прогноз возможных проблем

**Задать вопрос боту:**
```
/ask Почему растет память Redis?
```
Бот проанализирует текущее состояние Redis и ответит на ваш вопрос.

**Подписаться на уведомления:**
```
/subscribe
```
Теперь вы будете получать автоматические уведомления о:
- Критических проблемах
- Остановке контейнеров
- Проблемах с производительностью
- Алертах из AlertManager

## Мониторинг сервисов

### NGINX (cdn-nginx)

Метрики:
- Активные соединения
- Запросы в минуту
- Cache hit rate
- Upstream response time
- Memory usage

Проверка: `/nginx`

### Redis (cdn-redis)

Метрики:
- Используемая память
- Количество ключей
- Hit/Miss rate
- Подключенные клиенты
- Операций в секунду

Проверка: `/redis`

### WebP Converter (cdn-webp-converter-async)

Метрики:
- Размер очереди
- Обработанные файлы
- Ошибки конвертации
- Время обработки
- Memory usage

Проверка: `/webp`

### SSHFS (cdn-sshfs)

Проверка:
- Статус монтирования
- Доступность удаленного сервера
- Проблемы с SSH подключением

Проверка: `/containers`

### Prometheus (cdn-prometheus)

Сбор метрик со всех exporters:
- nginx-exporter (порт 9113)
- redis-exporter (порт 9121)
- node-exporter (порт 9100)
- webp-converter (порт 9101)

Доступ: http://localhost:9090

### AlertManager (cdn-alertmanager)

Управление алертами:
- Получение активных алертов
- Создание silences
- Webhook уведомления

Проверка: `/alerts`

## AI-анализ и рекомендации

Бот использует **GPT-4o** для интеллектуального анализа системы.

### Что анализирует AI:

1. **Статус контейнеров**
   - Работающие/остановленные сервисы
   - Health checks
   - Проблемы с запуском

2. **Метрики производительности**
   - Нагрузка на Nginx
   - Использование памяти Redis
   - Размер очереди WebP конвертера
   - Системные метрики (CPU, RAM, Disk)

3. **Проблемы и аномалии**
   - Высокое использование ресурсов
   - Ошибки в логах
   - Проблемы с кешированием
   - Медленные запросы

4. **Рекомендации**
   - Оптимизация конфигурации
   - Настройка кеширования
   - Масштабирование ресурсов
   - Предотвращение проблем

## Безопасность

### Авторизация

Доступ к боту ограничен в `config.yml`:

```yaml
telegram:
  allowed_users: [142636541, 987654321]  # Список User ID
  admin_users: [142636541]               # Администраторы
```

Только указанные пользователи могут использовать бота.

### Права доступа

- Бот имеет доступ к Docker socket (read-only)
- Доступ к Prometheus (read-only)
- Доступ к AlertManager (read + create silences)
- OpenAI API key хранится в переменных окружения

### Рекомендации

1. Не публикуйте токены в репозитории
2. Используйте `.env` для чувствительных данных
3. Ограничьте список `allowed_users`
4. Регулярно обновляйте бота и зависимости

## Troubleshooting

### Бот не запускается

```bash
# Проверьте логи
docker compose logs telegram-bot

# Проверьте переменные окружения
docker compose exec telegram-bot env | grep -E "TELEGRAM|OPENAI"

# Проверьте конфигурацию
docker compose exec telegram-bot cat /app/config.yml
```

### Бот не отвечает на команды

1. Проверьте, что ваш User ID в `allowed_users`
2. Убедитесь, что бот запущен: `docker compose ps telegram-bot`
3. Проверьте сетевое подключение к Docker socket

### AI-анализ не работает

1. Проверьте OPENAI_API_KEY
2. Убедитесь, что у вас есть доступ к GPT-4o
3. Проверьте баланс в OpenAI аккаунте
4. Посмотрите логи: `docker compose logs telegram-bot | grep -i openai`

### Метрики не отображаются

1. Убедитесь, что Prometheus запущен: `docker compose ps prometheus`
2. Проверьте доступность: `curl http://localhost:9090/api/v1/status`
3. Проверьте exporters: `docker compose ps | grep exporter`

## Обновление

```bash
# Остановить бота
docker compose stop telegram-bot

# Обновить код
git pull origin main

# Пересобрать образ
docker compose build telegram-bot

# Запустить бота
docker compose up -d telegram-bot

# Проверить логи
docker compose logs -f telegram-bot
```

## Лицензия и контакты

**Автор**: Chibilyaev Alexandr
**Email**: info@aachibilyaev.com
**Компания**: AAChibilyaev LTD

**Проект**: Bitrix CDN Monitoring Bot
**Версия**: 2.0.0
**Дата**: 2025-01-22

---

**Powered by:**
- Python 3.12
- python-telegram-bot 21.7
- OpenAI GPT-4o
- Docker API
- Prometheus
- Redis

Made with ❤️ for Bitrix CDN infrastructure monitoring
