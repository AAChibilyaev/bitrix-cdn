FROM python:3.12-alpine

# Установка системных зависимостей
RUN apk add --no-cache \
    curl \
    bash \
    tzdata \
    gcc \
    musl-dev \
    libffi-dev

# Установка рабочей директории
WORKDIR /app

# Копирование requirements и установка Python зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование исходного кода
COPY bot/ ./bot/
COPY config.yml .
COPY mypy.ini .

# Создание пользователя для безопасности
RUN adduser -D -s /bin/bash telegram-bot
RUN chown -R telegram-bot:telegram-bot /app

# Проверка типов (опционально, можно отключить в продакшене)
RUN mypy bot/ --config-file mypy.ini || echo "Type checking completed with warnings"

# Не переключаемся на пользователя, чтобы иметь доступ к Docker socket
# USER telegram-bot

# Команда запуска (основная версия)
CMD ["python", "-m", "bot.main"]
