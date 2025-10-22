# 🤖 Настройка Telegram Bot для мониторинга CDN

## 📋 Предварительные требования

### 1. Создание Telegram бота
1. Откройте Telegram и найдите [@BotFather](https://t.me/BotFather)
2. Отправьте команду `/newbot`
3. Введите имя бота (например: "Bitrix CDN Monitor")
4. Введите username бота (например: "bitrix_cdn_monitor_bot")
5. Скопируйте полученный токен

### 2. Получение OpenAI API ключа
1. Перейдите на [OpenAI Platform](https://platform.openai.com/)
2. Войдите в аккаунт или создайте новый
3. Перейдите в раздел "API Keys"
4. Создайте новый API ключ
5. Скопируйте ключ

## ⚙️ Настройка переменных окружения

### Создайте файл .env в корне проекта:
```bash
cd /home/aac/bitrix-cdn
nano .env
```

### Добавьте следующие переменные:
```env
# Redis Configuration
REDIS_PASSWORD=bitrix_cdn_secure_2024

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
OPENAI_API_KEY=your_openai_api_key_here

# CDN Domain
CDN_DOMAIN=cdn.termokit.ru
```

**Замените:**
- `your_telegram_bot_token_here` на токен от BotFather
- `your_openai_api_key_here` на ваш OpenAI API ключ

## 🚀 Запуск Telegram бота

### 1. Сборка образа (уже выполнена)
```bash
./docker-manage.sh telegram-bot build
```

### 2. Запуск бота
```bash
./docker-manage.sh telegram-bot start
```

### 3. Проверка статуса
```bash
./docker-manage.sh telegram-bot status
```

### 4. Просмотр логов
```bash
./docker-manage.sh telegram-bot logs
```

## 🔧 Управление ботом

### Доступные команды:
```bash
# Запуск
./docker-manage.sh telegram-bot start

# Остановка
./docker-manage.sh telegram-bot stop

# Перезапуск
./docker-manage.sh telegram-bot restart

# Просмотр логов
./docker-manage.sh telegram-bot logs

# Статус
./docker-manage.sh telegram-bot status

# Пересборка образа
./docker-manage.sh telegram-bot build
```

## 📱 Использование бота

### 1. Найдите вашего бота в Telegram
- Поищите по username, который вы указали при создании
- Или используйте ссылку: `https://t.me/your_bot_username`

### 2. Начните общение
- Отправьте `/start` для начала работы
- Используйте `/help` для списка команд

### 3. Основные команды
- `/status` - общий статус системы
- `/nginx` - информация о Nginx
- `/redis` - статистика Redis
- `/webp` - статус WebP конвертера
- `/containers` - список контейнеров
- `/health` - health checks
- `/cache` - статистика кеширования

### 4. AI-анализ и интерактивные команды
- `/analyze` - AI-анализ системы
- `/ask [вопрос]` - задать вопрос боту о системе
- `/code` - анализ кода и конфигураций
- `/debug` - детальная диагностика
- `/suggest` - рекомендации по оптимизации
- `/report` - полный отчет
- `/alerts` - текущие алерты
- `/subscribe` - подписка на уведомления

## 🔒 Безопасность

### Ограничение доступа
По умолчанию бот доступен всем пользователям. Для ограничения доступа:

1. Отредактируйте файл `docker/telegram-bot/config.yml`
2. Добавьте список разрешенных пользователей и групп:
```yaml
telegram:
  allowed_users: [123456789, 987654321]  # Ваши chat_id
  allowed_groups: [-1001234567890]       # ID групп (отрицательные числа)
  admin_users: [123456789]               # Администраторы с расширенными правами
```

3. Перезапустите бота:
```bash
./docker-manage.sh telegram-bot restart
```

### Групповое использование
Бот поддерживает работу в группах:

1. **Добавьте бота в группу** как администратора
2. **Получите ID группы**:
   - Добавьте бота в группу
   - Отправьте любое сообщение
   - Посмотрите в логи бота - там будет ID группы (отрицательное число)
3. **Настройте доступ** в config.yml:
```yaml
telegram:
  allowed_groups: [-1001234567890]  # ID вашей группы
```

### Интерактивные возможности
Бот поддерживает интерактивный анализ:

- **`/ask "Почему медленно работает Redis?"`** - задать вопрос о системе
- **`/code`** - анализ конфигураций и логов
- **`/debug`** - детальная диагностика проблем
- **`/suggest`** - рекомендации по оптимизации

### Получение chat_id
1. Напишите боту `/start`
2. Отправьте любое сообщение
3. Посмотрите в логи бота - там будет указан ваш chat_id

## 🐛 Устранение неполадок

### Бот не отвечает
1. Проверьте статус: `./docker-manage.sh telegram-bot status`
2. Проверьте логи: `./docker-manage.sh telegram-bot logs`
3. Убедитесь, что токен правильный
4. Перезапустите бота: `./docker-manage.sh telegram-bot restart`

### Ошибки подключения
1. Проверьте, что все сервисы CDN запущены:
```bash
./docker-manage.sh status
```

2. Убедитесь, что Prometheus и Redis работают:
```bash
curl http://localhost:9090/api/v1/status
curl http://localhost:6379
```

### AI-анализ не работает
1. Проверьте OpenAI API ключ
2. Убедитесь, что у вас есть кредиты на OpenAI
3. Проверьте логи на ошибки API

## 📊 Мониторинг бота

### Логи
```bash
# Просмотр логов в реальном времени
./docker-manage.sh telegram-bot logs

# Просмотр последних 100 строк
docker logs --tail 100 cdn-telegram-bot
```

### Метрики
Бот интегрирован с Prometheus и отправляет метрики на порт 9101.

### Уведомления
Бот автоматически отправляет уведомления о:
- Критических проблемах
- Остановке сервисов
- Высокой нагрузке
- Проблемах с кешем

## 🔄 Обновление бота

### Обновление кода
1. Внесите изменения в код
2. Пересоберите образ:
```bash
./docker-manage.sh telegram-bot build
```

3. Перезапустите бота:
```bash
./docker-manage.sh telegram-bot restart
```

### Обновление зависимостей
1. Отредактируйте `docker/telegram-bot/requirements.txt`
2. Пересоберите образ:
```bash
./docker-manage.sh telegram-bot build
```

## 📞 Поддержка

При возникновении проблем:
1. Проверьте логи бота
2. Убедитесь в правильности токенов
3. Проверьте статус всех сервисов CDN
4. Обратитесь к документации в `docker/telegram-bot/README.md`

---

**Автор**: Chibilyaev Alexandr <info@aachibilyaev.com>  
**Компания**: AAChibilyaev LTD  
**Версия**: 1.0.0
