FROM alpine:3.19

# Установка SSHFS и зависимостей
RUN apk add --no-cache \
    sshfs \
    openssh-client \
    fuse \
    bash \
    supervisor

# Создание директорий
RUN mkdir -p /mnt/bitrix \
    /var/log/sshfs \
    /root/.ssh

# Копирование скриптов
COPY mount.sh /usr/local/bin/mount.sh
COPY supervisord.conf /etc/supervisord.conf

# Установка прав
RUN chmod +x /usr/local/bin/mount.sh \
    && chmod 700 /root/.ssh

# Запуск через supervisor для автоматического перезапуска
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisord.conf"]
