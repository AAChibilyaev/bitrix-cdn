Автор: AAChibilyaev <info@aachibilyaev.com>  
  

# Интеграция с 1С-Битрикс

В этом документе описаны шаги по подключению CDN (aac.local) к сайту на базе 1С‑Битрикс и переносу медиа-файлов из папки `/upload` в объектное хранилище MinIO.

---

## 1. Настройка домена CDN в Битрикс

1. Откройте административную панель Битрикс:  
   **Настройки** → **Инструменты** → **Управление CDN**.  
2. В поле **Адрес CDN** введите ваш домен, например `https://aac.local`.  
3. Сохраните изменения.

> При таком подходе все ссылки на ресурсы `/upload/...` будут автоматически заменяться на `https://aac.local/upload/...`.

---

## 2. Ручная настройка через .settings.php

В случае использования кастомного подключения, добавьте в файл `/bitrix/.settings.php` в секцию `config`:

```php
'config' => [
    // ...
    'upload_dir' => '/upload',
    'upload_url' => 'https://aac.local/upload',
    'cdn_server' => 'https://aac.local',
],
```

Или определите константу в `prepend.php`:

```php
define('BX_CDN_SERVER', 'https://aac.local');
```

---

## 3. Миграция существующих медиа-файлов

1. Установите MinIO Client (`mc`) и настройте alias:

   ```bash
   mc alias set backup_minio http://localhost:9000 \
     $MINIO_ROOT_USER $MINIO_ROOT_PASSWORD --api S3v4
   ```

2. Выполните зеркалирование содержимого `/upload` в бакет:

   ```bash
   mc mirror --overwrite /path/to/bitrix/upload/ \
     backup_minio/$MINIO_BUCKET_NAME/upload/
   ```

3. После миграции убедитесь, что файлы доступны по URL:

   ```
   https://aac.local/upload/путь/к/файлу.jpg
   ```

---

## 4. Права доступа и безопасность

- По умолчанию бакет `MINIO_BUCKET_NAME` настроен на публичный доступ, чтобы любые браузеры могли загружать медиа.  
- При необходимости ограничьте доступ через временные URL или подписи (`signed URLs`) средствами MinIO.

---

## 5. Кросс-ссылки и дополнительные материалы

- См. [Конфигурация сервисов](configuration.md) для общего описания Docker Compose и Nginx.  
- См. [Резервное копирование и восстановление](backup-restore.md) для переноса и восстановления `/upload`.  
- Общая документация доступна в [README](../README.md).
