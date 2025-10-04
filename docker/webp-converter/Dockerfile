FROM alpine:3.19

# Создание непривилегированного пользователя
RUN addgroup -g 1000 webp && \
    adduser -D -s /bin/sh -u 1000 -G webp webp

# Установка необходимых пакетов
RUN apk add --no-cache \
    bash \
    libwebp-tools \
    imagemagick \
    inotify-tools \
    findutils \
    coreutils \
    python3 \
    py3-pip \
    py3-pillow \
    redis

# Установка Python библиотек для продвинутой обработки
RUN pip3 install --no-cache-dir --break-system-packages \
    redis \
    Pillow \
    watchdog

# Создание директорий с правильными правами
RUN mkdir -p /var/cache/webp /var/log/converter /app && \
    chown -R webp:webp /var/cache/webp /var/log/converter /app

# Копирование скриптов
COPY --chown=webp:webp converter.py /app/converter.py
COPY --chown=webp:webp entrypoint.sh /app/entrypoint.sh

# Установка прав
RUN chmod +x /app/entrypoint.sh /app/converter.py

# Переключение на непривилегированного пользователя
USER webp

WORKDIR /app

# Запуск конвертера
ENTRYPOINT ["/app/entrypoint.sh"]
