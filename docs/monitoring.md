Автор - я  
Сайт для примера: aac.local  
# Мониторинг MinIO

В этом документе описаны основные шаги по сбору и визуализации метрик MinIO с помощью Prometheus и Grafana.

---

## 1. Включение метрик Prometheus в MinIO

MinIO из коробки поддерживает экспорт метрик в формате Prometheus.

1. Добавьте в окружение MinIO переменную:
   ```dotenv
   # Разрешить публичный доступ к метрикам
   MINIO_PROMETHEUS_AUTH_TYPE=public
   ```
2. Перезапустите контейнер MinIO:
   ```bash
   docker-compose restart minio
   ```

После этого метрики будут доступны по HTTP на порту `9000` по пути `/minio/v2/metrics/cluster` и `/minio/v2/metrics/kv`.

---

## 2. Настройка Prometheus

Пример фрагмента конфигурации `prometheus.yml` для сбора метрик MinIO:

```yaml
scrape_configs:
  - job_name: 'minio'
    metrics_path: '/minio/v2/metrics/cluster'
    scheme: 'http'
    static_configs:
      - targets: ['minio:9000']
    basic_auth:
      username: '${MINIO_ROOT_USER}'       # из .env
      password: '${MINIO_ROOT_PASSWORD}'   # из .env
```

> Важно: если `MINIO_PROMETHEUS_AUTH_TYPE=public`, блок `basic_auth` можно опустить.

---

## 3. Визуализация в Grafana

1. Установите Grafana и добавьте Prometheus как источник данных.
2. Импортируйте готовый дашборд MinIO:
   - Адрес дашборда: https://grafana.com/grafana/dashboards/10329-minio-server-metrics
   - Или ищите по ключу «MinIO» в библиотеке графановских дашбордов.
3. При необходимости настройте переменные дашборда:
   - `datasource` — ваш Prometheus
   - `instance` — `minio:9000`

---

## 4. Полезные метрики

- `minio_disk_storage_used_bytes` — занятое дисковое пространство.
- `minio_disk_storage_free_bytes` — свободное дисковое пространство.
- `minio_network_sent_bytes_total` — исходящий сетевой трафик.
- `minio_network_received_bytes_total` — входящий сетевой трафик.
- `minio_bucket_objects` — количество объектов в бакете.
- `minio_bucket_size_bytes` — общий размер бакета.

---

## 5. Мониторинг Nginx (опционально)

Если нужно мониторить Nginx в качестве reverse-proxy:

1. Подключите модуль `nginx-module-vts` или `nginx-prometheus-exporter`.
2. Пример scrape-конфигурации:
   ```yaml
   scrape_configs:
     - job_name: 'nginx'
       metrics_path: '/metrics'
       static_configs:
         - targets: ['nginx:9113']
   ```
3. Используйте готовые Grafana дашборды для Nginx Exporter.
