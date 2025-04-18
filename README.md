# Автор: AAChibilyaev <info@aachibilyaev.com>
# Dockerized CDN с MinIO, Nginx и Certbot

Этот проект предоставляет решение для развёртывания самоподдерживаемой сети доставки контента (CDN) на основе Docker и Docker Compose. Используются:

* **MinIO:** S3-совместимое объектное хранилище для хранения медиа-ресурсов.
* **Nginx:** веб-сервер и обратный прокси для обслуживания объектов из MinIO и терминaции SSL.
* **Certbot:** автоматическое получение и обновление SSL-сертификатов от Let's Encrypt.

## Возможности

* Полная контейнеризация для простого развёртывания и управления.
* Поддержка S3-совместимого хранилища через MinIO.
* HTTPS с автоматическим получением и продлением сертификатов Let's Encrypt.
* Скрипты для резервного копирования и восстановления данных MinIO.
* Документация по мониторингу и устранению неполадок.

## Выбор стека и обоснование

Перед началом работы я проанализировал несколько решений для CDN: облачные S3-сервисы (AWS S3, DigitalOcean Spaces), S3-совместимые платформы (Ceph, MinIO), а также классические прокси-сервера. В результате оценки по критериям производительности, стоимости, масштабируемости и простоты интеграции с 1С-Битрикс я остановился на связке MinIO + Nginx + Certbot. Основные преимущества выбранного решения:
- MinIO: бесплатная S3-совместимая платформа с возможностью локального хранения и удобной миграции данных.
- Nginx: гибкая настройка кэширования и SSL-терминации для максимальной производительности.
- Certbot: автоматическое получение и обновление сертификатов от Let's Encrypt без дополнительных затрат.

## Требования

* **Docker:** версия 20.10+  
* **Docker Compose:** версия 1.29+  
* **MinIO Client (`mc`):** рекомендуется для работы с MinIO (необязательно).  
* **Доменное имя:** должно указывать на IP сервера (A‑запись для порта 80/443).

## Настройка

1. **Клонирование репозитория:**
   ```bash
   git clone <URL_репозитория>
   cd cdn.termokit.ru
   ```

2. **Создание файла переменных окружения:**
   - Для локальной разработки:
     ```bash
     cp .env.example .env
     # В файле .env укажите:
     # CDN_DOMAIN=aac.local
     # SSL_EMAIL=info@aachibilyaev.com
     ```
   - Для продакшена:
     ```bash
     cp .env.example .env.prod
     mv .env.prod .env
     # В файле .env укажите:
     # CDN_DOMAIN=cdn.termokit.ru
     # SSL_EMAIL=info@aachibilyaev.com
     ```
   Обязательные переменные:  
   `MINIO_ROOT_USER`, `MINIO_ROOT_PASSWORD`, `MINIO_BUCKET_NAME`, `CDN_DOMAIN`, `SSL_EMAIL`, `TZ`.

3. **Создание бакета (если необходимо):**
   ```bash
   mc alias set local http://localhost:9000 $MINIO_ROOT_USER $MINIO_ROOT_PASSWORD --api S3v4
   mc mb local/$MINIO_BUCKET_NAME
   ```

## Запуск

1. **Сборка и запуск сервисов:**
   ```bash
   docker-compose down -v
   docker-compose up -d --build
   ```

2. **Первичное получение SSL-сертификата:**
   ```bash
   docker-compose run --rm certbot certonly \
     --webroot -w /var/www/certbot \
     -d ${CDN_DOMAIN} \
     --email ${SSL_EMAIL} \
     --agree-tos --non-interactive
   ```

3. **Перезапуск Nginx для загрузки сертификатов:**
   ```bash
   docker-compose restart nginx
   ```

4. **Остановка сервисов:**
   ```bash
   docker-compose down
   ```

5. **Просмотр логов:**
   ```bash
   docker-compose logs -f nginx
   docker-compose logs -f minio
   docker-compose logs -f certbot
   ```

## Резервное копирование и восстановление

* **Резервное копирование:**
  ```bash
  ./scripts/backup.sh
  ```
* **Восстановление:**
  ```bash
  ./scripts/restore.sh <путь_к_резервной_копии>
  ```

## Обзор сервисов

* **nginx:** обслуживает контент из MinIO, SSL-терминация.  
* **minio:** объектное хранилище, API порт 9000, консоль 9001.  
* **certbot:** управление сертификатами Let's Encrypt, автопродление.

## Дополнительная документация

* [Конфигурация](docs/configuration.md)  
* [Резервное копирование и восстановление](docs/backup-restore.md)  
* [Мониторинг](docs/monitoring.md)  
* [Устранение неполадок](docs/troubleshooting.md)
* [Интеграция с 1С-Битрикс](docs/bitrix-integration.md)

## Лицензия

MIT License
