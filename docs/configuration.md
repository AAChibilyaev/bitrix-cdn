Автор - я  
Сайт для примера: aac.local  

# Конфигурация сервисов

В данном документе описаны основные компоненты и параметры конфигурации для запуска CDN на базе Docker Compose.

---

## 1. Переменные окружения (.env)

Файл `.env` хранит параметры, необходимые для работы сервисов. Для упрощения настройки используйте шаблон `.env.example`.

Структура и описание переменных:

```dotenv
# --- Конфигурация MinIO ---
MINIO_ROOT_USER=minioadmin           # Корневой пользователь MinIO (по умолчанию minioadmin)
MINIO_ROOT_PASSWORD=<secure_pass>    # Корневой пароль MinIO (обязательно замените)
MINIO_BUCKET_NAME=my-cdn-bucket      # Имя бакета для хранения файлов CDN

# --- Конфигурация CDN и SSL ---
CDN_DOMAIN=aac.local                 # Домен для CDN (пример aac.local)
SSL_EMAIL=youremail@example.com      # Email для регистрации и уведомлений Let's Encrypt

# --- Общие настройки ---
TZ=Europe/Moscow                     # Часовой пояс контейнеров (например, Europe/Moscow)
```

> Важно: после копирования `.env.example` в `.env` заменить `<secure_pass>`, указать корректные значения `CDN_DOMAIN` и `SSL_EMAIL`.

---

## 2. Docker Compose (`docker-compose.yml`)

Определены три сервиса:

1. **nginx**  
   - Сборка образа из каталога `nginx/`.  
   - Использует переменные окружения из файла `.env`.  
   - Точки монтирования:
     - `./nginx/conf.d` → `/etc/nginx/conf.d` (только чтение)
     - `./nginx/ssl` → `/etc/letsencrypt` (сертификаты)
     - `./logs/nginx` → `/var/log/nginx` (логи)
     - `nginx-cache` → `/var/cache/nginx` (кэш)
     - `./nginx/www` → `/var/www/certbot` (ACME challenge)
   - Зависит от сервиса `minio`.
   - Политика перезапуска: `unless-stopped`.

2. **minio**  
   - Образ: `minio/minio:latest`.  
   - Переменные окружения из `.env`.  
   - Команда запуска:  
     ```
     server /data --console-address ":9001"
     ```
   - Точки монтирования:
     - `minio-data` (volume) → `/data`
   - Порты:
     - `9000:9000` — API MinIO
     - `9001:9001` — Консоль управления
   - Healthcheck:
     ```yaml
     healthcheck:
       test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
       interval: 30s
       timeout: 3s
       retries: 3
     ```
   - Политика перезапуска: `unless-stopped`.

3. **certbot**  
   - Образ: `certbot/certbot:latest`.  
   - Переменные окружения из `.env`.  
   - Точки монтирования:
     - `./nginx/ssl` → `/etc/letsencrypt`
     - `./nginx/www` → `/var/www/certbot`
   - Команда запуска автообновления сертификатов:
     ```
     sh -c "while true; do certbot renew --quiet; sleep 12h; done"
     ```
   - Зависит от сервиса `nginx` (для вебroot проверки).
   - Политика перезапуска: `unless-stopped`.

```bash
docker-compose up -d --build
```

---

## 3. Nginx

### 3.1 Dockerfile (`nginx/Dockerfile`)

```dockerfile
FROM nginx:stable-alpine
# Устанавливаем gettext и openssl для подстановки переменных и создания ключей
RUN apk add --no-cache gettext openssl

# Копируем шаблон и скрипт запуска
COPY conf.d/cdn.conf.template /etc/nginx/templates/cdn.conf.template
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

ENTRYPOINT ["entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"]
```

### 3.2 Скрипт запуска (`nginx/entrypoint.sh`)

```sh
#!/bin/sh
# Подстановка переменных окружения и генерация конечного конфига
envsubst '$CDN_DOMAIN' \
  < /etc/nginx/templates/cdn.conf.template \
  > /etc/nginx/conf.d/cdn.conf

# Запуск Nginx в фоновом режиме
exec "$@"
```

### 3.3 Шаблон конфигурации (`nginx/conf.d/cdn.conf.template`)

- Определение зоны кэша
- HTTP → HTTPS редирект и ACME challenge
- SSL-настройки для Let's Encrypt
- Безопасные заголовки
- Прокси на MinIO с кэшированием
- CORS и логирование

> Полная конфигурация доступна в файле `nginx/conf.d/cdn.conf.template`.

---

## 4. Хранилище MinIO

- Порт API: `9000`
- Консоль управления: `9001`
- Данные сохраняются в Docker volume `minio-data`.
- Для доступа из CLI используйте `mc`:
  ```bash
  mc alias set local http://localhost:9000 $MINIO_ROOT_USER $MINIO_ROOT_PASSWORD --api S3v4
  mc ls local/$MINIO_BUCKET_NAME
  ```

---

## 5. Certbot (Let's Encrypt)

1. Первичное получение сертификата:
   ```bash
   docker-compose run --rm certbot certonly \
     --webroot -w /var/www/certbot \
     -d $CDN_DOMAIN \
     --email $SSL_EMAIL \
     --agree-tos --non-interactive
   ```
2. Перезапуск Nginx для загрузки новых сертификатов:
   ```bash
   docker-compose restart nginx
   ```
3. Автообновление сертификатов запускается контейнером `certbot` каждые 12 часов.

---

## 6. Логирование и кэш

- Логи Nginx сохраняются в `logs/nginx`.
- Кэш Nginx хранится в volume `nginx-cache`.
- Просмотр логов в реальном времени:
  ```bash
  docker-compose logs -f nginx
  ```

---

## 7. Интеграция с 1С-Битрикс

См. файл [docs/bitrix-integration.md](docs/bitrix-integration.md) для настройки подключения CDN и миграции медиа-файлов из `/upload`.
