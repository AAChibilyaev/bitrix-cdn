Автор: AAChibilyaev <info@aachibilyaev.com>  
  
# Решение частых проблем

В этом документе описаны способы диагностики и устранения распространённых ошибок при работе с CDN на базе MinIO, Nginx и Certbot.

---

## 1. Ошибки MinIO "Access Denied"

### Возможные причины
1. Неправильные учётные данные  
2. Проблемы с alias в клиенте mc  
3. Отсутствие прав на бакет или объект  

### Шаги устранения
1. Проверьте переменные окружения в `.env`:  
   ```bash
   echo $MINIO_ROOT_USER  # должен соответствовать вашему MINIO_ROOT_USER
   echo $MINIO_ROOT_PASSWORD  # MINIO_ROOT_PASSWORD
   ```
2. Проверьте alias mc:  
   ```bash
   mc alias list
   mc alias remove myalias && \
   mc alias set myalias http://localhost:9000 $MINIO_ROOT_USER $MINIO_ROOT_PASSWORD --api S3v4
   ```
3. Убедитесь, что бакет существует и у пользователя есть к нему доступ:  
   ```bash
   mc ls myalias/$MINIO_BUCKET_NAME
   ```
4. Если бакет отсутствует, создайте его:  
   ```bash
   mc mb myalias/$MINIO_BUCKET_NAME
   ```

---

## 2. Проблемы с сертификатами Let's Encrypt

### Симптомы
- Certbot выдаёт ошибки валидации HTTP-01  
- Nginx не загружает сертификат  
- Сертификат не обновляется  

### Проверка и решение
1. Удостоверьтесь, что DNS A‑запись домена `CDN_DOMAIN` указывает на IP сервера.  
2. Откройте порты 80 и 443 на брандмауэре/хосте.  
3. Проверьте, что вручную можно получить challenge:  
   ```bash
   curl -I http://<CDN_DOMAIN>/.well-known/acme-challenge/test-file
   ```
4. Запустите принудительное получение:  
   ```bash
   docker-compose run --rm certbot certonly \
     --webroot -w /var/www/certbot \
     -d $CDN_DOMAIN \
     --email $SSL_EMAIL \
     --agree-tos --non-interactive --force-renewal
   ```
5. Проверьте логи Nginx и Certbot:  
   ```bash
   docker-compose logs nginx
   docker-compose logs certbot
   ```

---

## 3. Ошибки Nginx (502 Bad Gateway / 504 Gateway Timeout)

### Возможные причины
- MinIO контейнер не запущен или упал  
- Неправильный upstream в proxy_pass  
- Сетевые проблемы в Docker-сети  

### Шаги устранения
1. Убедитесь, что контейнер MinIO работает:  
   ```bash
   docker-compose ps | grep minio
   ```
2. Проверьте доступность MinIO изнутри Nginx:  
   ```bash
   docker-compose exec nginx ping -c 3 minio
   docker-compose exec nginx curl -I http://minio:9000/minio/health/live
   ```
3. В конфигурации `proxy_pass` должно быть `http://minio:9000`.  
4. Увеличьте таймауты в `nginx/conf.d/cdn.conf.template` при необходимости (proxy_read_timeout, proxy_connect_timeout).

---

## 4. CORS ошибки

### Симптомы
- Браузер блокирует запросы к CDN  
- Ошибки вида `Access-Control-Allow-Origin`  

### Решение
1. Проверьте, что в блоке `location /` присутствуют заголовки:  
   ```nginx
   add_header 'Access-Control-Allow-Origin' "$http_origin" always;
   add_header 'Access-Control-Allow-Methods' 'GET, OPTIONS' always;
   ```
2. Убедитесь, что клиентский запрос содержит правильный Origin.  
3. Для статических ресурсов можно ограничить список доменов вместо `$http_origin`.

---

## 5. Проблемы скриптов backup.sh и restore.sh

### Симптомы
- Скрипт завершается с ошибкой `mc: command not found`  
- Ошибки доступа к `.env`  
- Неправильная директория бэкапа  

### Решение
1. Установите MinIO Client (`mc`) в PATH:  
   ```bash
   wget https://dl.min.io/client/mc/release/linux-amd64/mc
   chmod +x mc && mv mc /usr/local/bin/
   ```
2. Проверьте, что скрипты имеют право на исполнение:  
   ```bash
   chmod +x scripts/backup.sh scripts/restore.sh
   ```
3. Убедитесь, что `.env` в корне проекта и содержит все переменные.  
4. При необходимости явно указывайте путь до backup-каталога:  
   ```bash
   ./scripts/restore.sh ./backups/my-cdn-bucket-2025-04-18_03-00-00
   ```

---

## 6. Общая диагностика

1. Сбор логов всех сервисов:  
   ```bash
   docker-compose logs --tail=100
   ```
2. Проверка статуса контейнеров:  
   ```bash
   docker-compose ps
   ```
3. Проверка использования диска и памяти на хосте:  
   ```bash
   df -h
   free -m
   ```
4. При необходимости перезапускайте сервисы или весь стек:  
   ```bash
   docker-compose restart
   ```

Все конфигурации и скрипты снабжены подробными комментариями на русском языке.
