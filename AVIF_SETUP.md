# AVIF Support Setup for Bitrix CDN

## Обзор

Добавлена поддержка формата AVIF в CDN сервер для максимального сжатия изображений. AVIF обеспечивает лучшее сжатие по сравнению с WebP и JPEG.

## Что добавлено

### 1. Конвертер изображений
- Поддержка конвертации в AVIF формат
- Параллельная конвертация в WebP и AVIF
- Настраиваемое качество для каждого формата
- Умная логика определения необходимости конвертации

### 2. Nginx конфигурация
- Автоматическое определение поддержки AVIF браузером
- Приоритетная отдача AVIF → WebP → оригинал
- Правильные MIME-типы для AVIF
- Кэширование на 1 год

### 3. Скрипты управления
- `avif-ctl.sh` - управление AVIF конвертером
- `test-avif-conversion.py` - тестирование конвертации

## Использование

### Запуск AVIF конвертера

```bash
# Запуск сервиса
./avif-ctl.sh start

# Проверка статуса
./avif-ctl.sh stats

# Просмотр логов
./avif-ctl.sh logs

# Тестирование AVIF конвертации
./avif-ctl.sh test-avif
```

### Управление форматами

```bash
# Включить только AVIF
./avif-ctl.sh enable-avif
./avif-ctl.sh disable-webp

# Включить только WebP
./avif-ctl.sh enable-webp
./avif-ctl.sh disable-avif

# Включить оба формата (по умолчанию)
./avif-ctl.sh enable-avif
./avif-ctl.sh enable-webp
```

### Тестирование

```bash
# Запуск тестов конвертации
python3 test-avif-conversion.py
```

## Конфигурация

### Переменные окружения

```bash
# Качество AVIF (по умолчанию 80)
AVIF_QUALITY=80

# Качество WebP (по умолчанию 85)
WEBP_QUALITY=85

# Включить/выключить форматы
ENABLE_AVIF=true
ENABLE_WEBP=true

# Минимальный размер файла для конвертации
WEBP_MIN_FILE_SIZE=10240
```

### Конфигурационный файл (config.yml)

```yaml
# WebP/AVIF Converter Default Configuration

# Image processing
webp_quality: 85
avif_quality: 80
min_file_size: 10240  # 10KB
extensions:
  - jpg
  - jpeg
  - png

# Format support
enable_webp: true
enable_avif: true

# Performance - MAXIMUM SPEED
worker_threads: 12
batch_size: 50
max_queue_size: 10000
rate_limit: 500  # files per minute
```

## Архитектура

### Логика отдачи изображений

1. **Браузер с поддержкой AVIF**: AVIF → WebP → оригинал
2. **Браузер с поддержкой WebP**: WebP → оригинал  
3. **Старый браузер**: оригинал

### Приоритет форматов

1. **AVIF** - лучшее сжатие, поддержка в современных браузерах
2. **WebP** - хорошее сжатие, широкая поддержка
3. **JPEG/PNG** - оригинальные форматы для совместимости

## Мониторинг

### Метрики Prometheus

```
# Количество конвертированных изображений
webp_images_converted_total

# Время конвертации
webp_conversion_duration_seconds

# Размеры файлов
webp_original_size_bytes
webp_webp_size_bytes

# Ошибки конвертации
webp_conversion_errors_total
```

### Health Checks

```bash
# Проверка здоровья
curl http://localhost:8088/health

# Проверка готовности
curl http://localhost:8088/ready

# Метрики
curl http://localhost:9101/metrics
```

## Производительность

### Ожидаемые результаты

- **AVIF**: на 20-50% меньше размер файла по сравнению с WebP
- **WebP**: на 25-35% меньше размер файла по сравнению с JPEG
- **Скорость конвертации**: AVIF медленнее WebP, но обеспечивает лучшее сжатие

### Рекомендации

1. **Качество AVIF**: 75-85 для оптимального баланса
2. **Качество WebP**: 80-90 для совместимости
3. **Минимальный размер**: 10KB для избежания конвертации мелких файлов

## Устранение неполадок

### Проблемы с конвертацией

```bash
# Проверка логов
./avif-ctl.sh logs

# Перезапуск сервиса
./avif-ctl.sh restart

# Проверка конфигурации
docker exec cdn-webp-converter cat /app/config.yml
```

### Проблемы с Nginx

```bash
# Проверка конфигурации
nginx -t

# Перезагрузка конфигурации
nginx -s reload

# Проверка логов
tail -f /var/log/nginx/cdn.error.log
```

## Браузерная поддержка

### AVIF
- Chrome 85+
- Firefox 93+
- Safari 16+
- Edge 85+

### WebP
- Chrome 23+
- Firefox 65+
- Safari 14+
- Edge 18+

## Обновления

Для обновления до новой версии с поддержкой AVIF:

```bash
# Остановка сервисов
./docker-manage.sh stop

# Обновление кода
git pull

# Пересборка образов
./docker-manage.sh build

# Запуск сервисов
./docker-manage.sh start
```

## Поддержка

При возникновении проблем:

1. Проверьте логи: `./avif-ctl.sh logs`
2. Проверьте конфигурацию: `./avif-ctl.sh stats`
3. Запустите тесты: `./avif-ctl.sh test-avif`
4. Проверьте мониторинг: `curl http://localhost:9101/metrics`
