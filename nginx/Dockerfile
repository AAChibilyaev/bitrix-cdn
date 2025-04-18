# Автор: AAChibilyaev <info@aachibilyaev.com>
# Базовый образ Nginx на Alpine для минимального размера
FROM nginx:stable-alpine

# Установка gettext для использования envsubst (подстановка переменных)
RUN apk add --no-cache gettext openssl

# Создаём директорию для шаблонов и копируем шаблон конфигурации Nginx
# Файл с расширением .template будет использоваться для подстановки переменных окружения
RUN mkdir -p /etc/nginx/templates
COPY conf.d/cdn.conf.template /etc/nginx/templates/cdn.conf.template

# Копирование скрипта запуска, который выполняет подстановку и старт Nginx
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# Точка входа: сначала подставляем переменные, затем запускаем Nginx
ENTRYPOINT ["entrypoint.sh"]
# Запуск Nginx в фореграунд-режиме
CMD ["nginx", "-g", "daemon off;"]
