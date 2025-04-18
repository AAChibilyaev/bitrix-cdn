#!/bin/bash
# Автор: AAChibilyaev <info@aachibilyaev.com>
#
# Скрипт восстановления MinIO-бакета из локальной резервной копии
#
# Описание:
# Копирует (mirror) содержимое директории резервной копии в бакет MinIO.
# Внимание: перезаписывает файлы в бакете, если они отличаются.
#
# Требования:
# - Установлен MinIO Client (mc) в PATH.
# - Файл .env в корне проекта содержит:
#     MINIO_ROOT_USER, MINIO_ROOT_PASSWORD, MINIO_BUCKET_NAME.
#
# Переменные окружения (.env):
#   MINIO_ROOT_USER     – корневой пользователь MinIO
#   MINIO_ROOT_PASSWORD – пароль пользователя MinIO
#   MINIO_BUCKET_NAME   – имя бакета для CDN-ресурсов
#   MINIO_ENDPOINT      – (необязательно) URL MinIO (по умолчанию http://localhost:9000)
#   BACKUP_SOURCE_DIR   – (необязательно) путь к директории резервной копии

set -euo pipefail

# Загружаем переменные из .env, если файл существует
ENV_FILE="$(dirname "$0")/../.env"
if [ -f "$ENV_FILE" ]; then
  # shellcheck disable=SC1090
  source "$ENV_FILE"
fi

# Определяем директорию резервной копии: аргумент или переменная окружения
if [ -n "${1:-}" ]; then
  BACKUP_SOURCE_DIR="$1"
elif [ -n "${BACKUP_SOURCE_DIR:-}" ]; then
  BACKUP_SOURCE_DIR="$BACKUP_SOURCE_DIR"
else
  echo "Ошибка: укажите директорию резервной копии." >&2
  echo "Использование: $0 <path_to_backup_directory>" >&2
  exit 1
fi

# Проверяем наличие директории
if [ ! -d "$BACKUP_SOURCE_DIR" ]; then
  echo "Ошибка: директория не найдена: $BACKUP_SOURCE_DIR" >&2
  exit 1
fi

# Проверяем обязательные переменные
: "${MINIO_ROOT_USER?Ошибка: MINIO_ROOT_USER не задан. Проверьте .env}"
: "${MINIO_ROOT_PASSWORD?Ошибка: MINIO_ROOT_PASSWORD не задан. Проверьте .env}"
: "${MINIO_BUCKET_NAME?Ошибка: MINIO_BUCKET_NAME не задан. Проверьте .env}"

# Параметры
MINIO_ENDPOINT="${MINIO_ENDPOINT:-http://localhost:9000}"
MC_ALIAS="restore_minio_$$"  # Уникальный алиас для mc

echo "=== Начало восстановления бакета: ${MINIO_BUCKET_NAME} ==="
echo "Источник: ${BACKUP_SOURCE_DIR}"
echo "MinIO endpoint: ${MINIO_ENDPOINT}"

# Настройка временного алиаса mc
mc alias set "${MC_ALIAS}" "${MINIO_ENDPOINT}" "${MINIO_ROOT_USER}" "${MINIO_ROOT_PASSWORD}" --api S3v4

# Выполнение mirror
echo "Запуск mc mirror: ${BACKUP_SOURCE_DIR}/ -> ${MC_ALIAS}/${MINIO_BUCKET_NAME}/"
mc mirror --overwrite "${BACKUP_SOURCE_DIR}/" "${MC_ALIAS}/${MINIO_BUCKET_NAME}/"

echo "=== Восстановление завершено ==="

# Удаление алиаса mc
mc alias remove "${MC_ALIAS}"
exit 0
