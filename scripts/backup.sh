#!/bin/bash
# Автор: AAChibilyaev <info@aachibilyaev.com>
#
# Скрипт резервного копирования MinIO-бакета
#
# Описание:
# Копирует (mirror) содержимое указанного бакета MinIO в локальную директорию с таймстампом.
# При повторном запуске перезаписывает изменённые файлы.
#
# Требования:
# - Установлен MinIO Client (mc) в PATH.
# - Файл переменных окружения .env находится в корне проекта.
#   и содержит MINIO_ROOT_USER, MINIO_ROOT_PASSWORD, MINIO_BUCKET_NAME.
#
# Переменные окружения (.env):
#   MINIO_ROOT_USER     – корневой пользователь MinIO (minioadmin по умолчанию)
#   MINIO_ROOT_PASSWORD – пароль пользователя MinIO
#   MINIO_BUCKET_NAME   – имя бакета для CDN-ресурсов
#   BACKUP_DIR          – (необязательно) базовая директория для бэкапов (по умолчанию "./backups")
#
set -euo pipefail

# Загружаем переменные из .env, если файл доступен
ENV_FILE="$(dirname "$0")/../.env"
if [ -f "${ENV_FILE}" ]; then
  # shellcheck disable=SC1090
  source "${ENV_FILE}"
fi

# Проверка обязательных переменных
: "${MINIO_ROOT_USER?Ошибка: MINIO_ROOT_USER не задан. Проверьте .env}"
: "${MINIO_ROOT_PASSWORD?Ошибка: MINIO_ROOT_PASSWORD не задан. Проверьте .env}"
: "${MINIO_BUCKET_NAME?Ошибка: MINIO_BUCKET_NAME не задан. Проверьте .env}"

# Настройка параметров
BACKUP_DIR="${BACKUP_DIR:-$(dirname "$0")/../backups}"
MINIO_ENDPOINT="${MINIO_ENDPOINT:-http://localhost:9000}"
MC_ALIAS="backup_minio_$$"  # Уникальный алиас для mc

echo "=== Начало резервного копирования бакета: ${MINIO_BUCKET_NAME} ==="

# Создаём директорию для бэкапов, если её нет
echo "Создаём базовую директорию: ${BACKUP_DIR}"
mkdir -p "${BACKUP_DIR}"

# Формируем директорию с таймстампом
TIMESTAMP=$(date +%Y-%m-%d_%H-%M-%S)
TARGET_DIR="${BACKUP_DIR}/${MINIO_BUCKET_NAME}-${TIMESTAMP}"
echo "Целевая директория: ${TARGET_DIR}"

# Конфигурируем временный алиас для mc
echo "Настройка временного алиаса mc: ${MC_ALIAS} -> ${MINIO_ENDPOINT}"
mc alias set "${MC_ALIAS}" "${MINIO_ENDPOINT}" "${MINIO_ROOT_USER}" "${MINIO_ROOT_PASSWORD}" --api S3v4

# Запускаем mirror
echo "Запуск mc mirror: ${MC_ALIAS}/${MINIO_BUCKET_NAME}/ -> ${TARGET_DIR}/"
mc mirror --overwrite "${MC_ALIAS}/${MINIO_BUCKET_NAME}/" "${TARGET_DIR}/"

# Отобразить размер бэкапа
SIZE=$(du -sh "${TARGET_DIR}" | cut -f1)
echo "Резервная копия создана: ${TARGET_DIR} (размер: ${SIZE})"

# Удаляем временный алиас
echo "Удаление алиаса mc: ${MC_ALIAS}"
mc alias remove "${MC_ALIAS}"

echo "=== Резервное копирование завершено ==="
