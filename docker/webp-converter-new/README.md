# WebP Converter Service

Асинхронный конвертер изображений в формат WebP для CDN сервера.

## Возможности

- ✅ Автоматическое обнаружение новых изображений (JPG, JPEG, PNG)
- ✅ Асинхронная конвертация в WebP с настраиваемым качеством
- ✅ Мониторинг через Prometheus метрики
- ✅ Health check endpoints (liveness & readiness)
- ✅ Graceful shutdown с завершением текущих задач
- ✅ Rate limiting для контроля нагрузки
- ✅ Retry логика при ошибках
- ✅ Структурированное JSON логирование (structlog)
- ✅ File watcher для real-time обработки

## Архитектура

```
┌─────────────────────────────────────────┐
│         WebP Converter Service          │
├─────────────────────────────────────────┤
│                                         │
│  ┌──────────┐  ┌────────────────────┐  │
│  │ Watcher  │→ │  Queue Manager     │  │
│  │(watchdog)│  │  (asyncio.Queue)   │  │
│  └──────────┘  └────────────────────┘  │
│                         ↓               │
│               ┌──────────────────┐      │
│               │  Worker Pool     │      │
│               │  (async tasks)   │      │
│               └──────────────────┘      │
│                         ↓               │
│               ┌──────────────────┐      │
│               │  Image Converter │      │
│               │  (Pillow)        │      │
│               └──────────────────┘      │
│                                         │
│  ┌────────────┐      ┌──────────────┐  │
│  │ Prometheus │      │ Health Check │  │
│  │ :9101      │      │ :8088        │  │
│  └────────────┘      └──────────────┘  │
└─────────────────────────────────────────┘
```

## Быстрый старт

### 1. Сборка и запуск

```bash
# Build
docker compose build webp-converter-async

# Start
docker compose up -d webp-converter-async

# Check logs
docker compose logs -f webp-converter-async
```

### 2. Проверка работы

```bash
# Health check
curl http://localhost:8088/health

# Readiness check
curl http://localhost:8088/ready

# Prometheus metrics
curl http://localhost:9101/metrics
```

## Конфигурация

Все настройки через environment variables в `docker-compose.yml`:

### Основные параметры

- `WEBP_QUALITY` - качество WebP (0-100, default: 85)
- `WEBP_WORKER_THREADS` - количество worker'ов (default: 4)
- `WEBP_MIN_FILE_SIZE` - минимальный размер файла (default: 10240 bytes)
- `WEBP_EXTENSIONS` - расширения для обработки (default: jpg,jpeg,png)

### Производительность

- `WEBP_RATE_LIMIT` - максимум файлов в минуту (default: 100)
- `WEBP_MAX_QUEUE_SIZE` - размер очереди (default: 1000)
- `WEBP_BATCH_SIZE` - размер batch'а (default: 10)

### Мониторинг

- `METRICS_PORT` - порт Prometheus (default: 9101)
- `HEALTH_PORT` - порт Health checks (default: 8088)
- `LOG_LEVEL` - уровень логирования (default: INFO)

## Мониторинг

### Prometheus Метрики

Доступны на `http://localhost:9101/metrics`:

```
# Счетчики
webp_images_converted_total     # Всего конвертировано
webp_images_skipped_total       # Пропущено (уже существуют)
webp_conversion_errors_total    # Ошибки конвертации

# Histogram
webp_conversion_duration_seconds # Время конвертации

# Summary
webp_original_size_bytes        # Размер оригиналов
webp_webp_size_bytes            # Размер WebP

# Gauge
webp_queue_size                 # Текущий размер очереди
webp_compression_ratio          # Коэффициент сжатия (%)
```

### Health Checks

- **Liveness**: `http://localhost:8088/health`
  Проверяет что сервис запущен

- **Readiness**: `http://localhost:8088/ready`
  Проверяет что watch директория доступна

### Grafana Dashboard

Импортируйте dashboard из:
`docker/grafana/provisioning/dashboards/webp-converter.json`

## Management Script

Используйте `webp-ctl.sh` для управления:

```bash
./webp-ctl.sh start      # Запуск
./webp-ctl.sh stop       # Остановка
./webp-ctl.sh restart    # Перезапуск
./webp-ctl.sh logs       # Просмотр логов
./webp-ctl.sh stats      # Статистика (Prometheus)
./webp-ctl.sh health     # Health check
./webp-ctl.sh ready      # Readiness check
./webp-ctl.sh build      # Пересборка образа
./webp-ctl.sh exec       # Shell в контейнере
```

## Логирование

Структурированные JSON логи в stdout:

```json
{
  "event": "Image converted",
  "level": "info",
  "timestamp": "2025-10-04T02:45:00.123456",
  "worker_id": 2,
  "file": "photo.jpg",
  "original_size": 163168,
  "webp_size": 7456,
  "compression": "95.4%",
  "duration": "0.45s"
}
```

## Troubleshooting

### Очередь растет

Увеличьте `WEBP_WORKER_THREADS` или уменьшите `WEBP_QUALITY`:

```yaml
environment:
  - WEBP_WORKER_THREADS=8
  - WEBP_QUALITY=75
```

### Высокая нагрузка на CPU

Уменьшите воркеры или установите limits:

```yaml
deploy:
  resources:
    limits:
      cpus: '2'
      memory: 1G
```

### Файлы не конвертируются

1. Проверьте права доступа:
```bash
ls -la /var/www/cdn/upload/resize_cache
```

2. Проверьте логи:
```bash
./webp-ctl.sh logs
```

3. Проверьте readiness:
```bash
./webp-ctl.sh ready
```

## Production Checklist

- [ ] Docker образ собран без ошибок
- [ ] Health checks работают
- [ ] Prometheus метрики доступны
- [ ] Логи в JSON формате
- [ ] Graceful shutdown тестирован
- [ ] Resource limits установлены
- [ ] Grafana dashboard настроен
- [ ] Права доступа www-data:www-data

## Архитектурные решения

### Почему asyncio?

- Эффективная обработка I/O операций
- Параллельная обработка множества файлов
- Graceful shutdown без потери задач

### Почему Pillow вместо cwebp CLI?

- Нативная Python интеграция
- Лучший контроль над процессом
- Обработка различных форматов изображений
- Retry логика на уровне Python

### Почему watchdog?

- Real-time обнаружение новых файлов
- Эффективнее периодического сканирования
- Кросс-платформенность

## Лицензия

MIT

## Автор

Chibilyaev Alexandr <info@aachibilyaev.com>
