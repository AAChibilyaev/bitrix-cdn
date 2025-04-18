#!/bin/sh
# Автор: AAChibilyaev <info@aachibilyaev.com>
#
# Скрипт запуска Nginx с подстановкой переменных окружения в конфигурацию.
#
# Использует envsubst для замены placeholder'ов в шаблоне конфигурации:
# - ${CDN_DOMAIN}

# Генерация самоподписанного сертификата, если нет полученных Let's Encrypt
if [ ! -f /etc/letsencrypt/live/${CDN_DOMAIN}/privkey.pem ]; then
    echo "Генерация самоподписанного сертификата для ${CDN_DOMAIN}"
    mkdir -p /etc/letsencrypt/live/${CDN_DOMAIN}
    openssl req -x509 -nodes -days 3650 \
        -subj "/CN=${CDN_DOMAIN}/O=Local/C=US" \
        -newkey rsa:2048 \
        -keyout /etc/letsencrypt/live/${CDN_DOMAIN}/privkey.pem \
        -out /etc/letsencrypt/live/${CDN_DOMAIN}/fullchain.pem
    cp /etc/letsencrypt/live/${CDN_DOMAIN}/fullchain.pem /etc/letsencrypt/live/${CDN_DOMAIN}/chain.pem
fi

# Подстановка значений переменных окружения в шаблон
envsubst '\$CDN_DOMAIN' < /etc/nginx/templates/cdn.conf.template > /etc/nginx/conf.d/cdn.conf

# Запуск Nginx в фореграунд-режиме (daemon off берётся из CMD)
exec "$@"
