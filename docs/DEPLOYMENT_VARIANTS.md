# 🚀 Варианты развертывания Bitrix CDN Server

**Автор**: Chibilyaev Alexandr | **AAChibilyaev LTD** | info@aachibilyaev.com

## 📋 Обзор вариантов

Проект поддерживает **3 варианта развертывания** для разных сценариев использования:

| Вариант | Файл | Описание | Когда использовать |
|---------|------|----------|-------------------|
| **🏭 Production** | `docker-compose.yml` | Полный стек с мониторингом | Production сервера |
| **🛠️ Development** | `docker-compose.dev.yml` | Упрощенная версия | Разработка, тестирование |
| **🏠 Local** | `docker-compose.local.yml` | Локальное тестирование | Отладка на localhost |

---

## 🏭 PRODUCTION ВАРИАНТ

### Файл: `docker-compose.yml`

**Полный стек для production серверов с максимальной надежностью и мониторингом.**

### Компоненты:
- ✅ **NGINX** (nginx:1.27-alpine) - основной веб-сервер
- ✅ **WebP Converter** (custom Python) - конвертация изображений
- ✅ **SSHFS** (custom) - монтирование файлов Битрикс
- ✅ **Redis** (redis:7.4-alpine) - кеширование метаданных
- ✅ **Varnish** (varnish:7.5-alpine) - HTTP кеш-акселератор
- ✅ **Prometheus** (prom/prometheus:v2.53.2) - сбор метрик
- ✅ **Grafana** (grafana/grafana:11.2.2) - дашборды
- ✅ **NGINX Exporter** - метрики NGINX
- ✅ **Redis Exporter** - метрики Redis
- ✅ **Node Exporter** - системные метрики
- ✅ **Certbot** - автообновление SSL сертификатов

### Особенности:
- 🛡️ **Максимальная безопасность** (read-only, no-new-privileges, tmpfs)
- 📊 **Полный мониторинг** всех компонентов
- 🔄 **Auto-recovery** при сбоях
- 🔒 **Автоматический SSL** через Let's Encrypt
- ⚡ **Высокая производительность** с Varnish

### Запуск:
```bash
docker-compose up -d
```

### Порты:
- **80, 443** - NGINX (HTTP/HTTPS)
- **8080** - Varnish (опционально)
- **3000** - Grafana (localhost only)
- **9090** - Prometheus (localhost only)
- **6379** - Redis (localhost only)
- **9113, 9121, 9100** - Exporters (localhost only)

---

## 🛠️ DEVELOPMENT ВАРИАНТ

### Файл: `docker-compose.dev.yml`

**Упрощенная версия без мониторинга для разработки и тестирования.**

### Компоненты:
- ✅ **NGINX** (nginx:1.27-alpine) - основной веб-сервер
- ✅ **WebP Converter** (custom Python) - конвертация изображений
- ✅ **SSHFS** (custom) - монтирование файлов Битрикс
- ✅ **Redis** (redis:7.4-alpine) - кеширование метаданных
- ❌ Без Varnish, Prometheus, Grafana, Exporters, Certbot

### Особенности:
- 🚀 **Быстрый запуск** - минимальное количество сервисов
- 🔧 **Простая отладка** - нет лишних компонентов
- 💾 **Меньше ресурсов** - экономия RAM и CPU
- 🌐 **Порт 8080** - не конфликтует с локальными сервисами

### Запуск:
```bash
docker-compose -f docker-compose.dev.yml up -d
```

### Порты:
- **8080** - NGINX (HTTP only)
- **6379** - Redis (localhost only)

---

## 🏠 LOCAL ВАРИАНТ

### Файл: `docker-compose.local.yml`

**Минимальная версия для локального тестирования без внешних зависимостей.**

### Компоненты:
- ✅ **NGINX** (nginx:1.27-alpine) - локальная конфигурация
- ✅ **WebP Converter** (без внешнего SSHFS)
- ❌ Без SSHFS, Redis, мониторинга

### Особенности:
- 💻 **Полностью локально** - без SSH подключений
- 📁 **Локальные файлы** - монтирует локальную директорию
- 🧪 **Тестирование алгоритмов** - проверка WebP конвертации
- ⚡ **Мгновенный запуск** - без сетевых зависимостей

### Запуск:
```bash
# Создать тестовую директорию с изображениями
mkdir -p ./test-images
# Поместить тестовые .jpg/.png файлы в ./test-images

docker-compose -f docker-compose.local.yml up -d
```

---

## ⚙️ NATIVE УСТАНОВКА

### Прямая установка на сервер без Docker

**Для максимального контроля и производительности.**

### Компоненты:
- ✅ **NGINX** - установка через apt
- ✅ **Python WebP Converter** - как systemd сервис
- ✅ **SSHFS** - через systemd сервис
- ✅ **Redis** - опционально
- ✅ **Prometheus/Grafana** - опционально

### Особенности:
- 🎯 **Максимальная производительность** - без Docker overhead
- 🔧 **Полный контроль** - прямая настройка всех сервисов
- 📊 **Системная интеграция** - с systemd и syslog
- 🛡️ **Безопасность** - настройка на уровне ОС

### Запуск:
```bash
make install
```

---

## 🎯 ВЫБОР ВАРИАНТА

### Используйте **Production** если:
- ✅ Это production сервер
- ✅ Нужен полный мониторинг
- ✅ Требуется максимальная надежность
- ✅ Планируется масштабирование

### Используйте **Development** если:
- 🛠️ Это тестовый/staging сервер
- 🛠️ Разрабатываете/настраиваете систему
- 🛠️ Хотите быстро проверить функциональность
- 🛠️ Ограничены в ресурсах

### Используйте **Local** если:
- 💻 Тестируете на локальной машине
- 💻 Отлаживаете WebP алгоритмы
- 💻 Изучаете как работает система
- 💻 Нет доступа к внешнему серверу

### Используйте **Native** если:
- ⚙️ Нужна максимальная производительность
- ⚙️ Docker недоступен или нежелателен
- ⚙️ Требуется глубокая интеграция с ОС
- ⚙️ Есть специфичные требования к безопасности

---

## 🔧 БЫСТРЫЙ СТАРТ ПО ВАРИАНТАМ

### Production (с мониторингом)
```bash
git clone <repo>
cd bitrix-cdn
cp .env.example .env  # настроить cdn.termokit.ru
./docker-manage.sh setup
docker-compose up -d
./docker-manage.sh ssl  # SSL сертификаты
```

### Development (быстро)
```bash
git clone <repo>
cd bitrix-cdn
cp .env.example .env  # настроить параметры
./docker-manage.sh setup
docker-compose -f docker-compose.dev.yml up -d
```

### Local (тестирование)
```bash
git clone <repo>
cd bitrix-cdn
mkdir test-images  # добавить тестовые изображения
docker-compose -f docker-compose.local.yml up -d
# Тест: http://localhost/test-image.jpg
```

### Native (на сервер)
```bash
git clone <repo>
cd bitrix-cdn
sudo make install  # автоматическая установка
sudo make health   # проверка
```

---

## 📊 СРАВНЕНИЕ ВАРИАНТОВ

| Критерий | Production | Development | Local | Native |
|----------|------------|-------------|-------|---------|
| **Время запуска** | 3-5 мин | 2-3 мин | 1 мин | 10-20 мин |
| **Потребление RAM** | 2-4 GB | 1-2 GB | 0.5-1 GB | 1-3 GB |
| **Количество контейнеров** | 11 | 4 | 2 | 0 |
| **Мониторинг** | ✅ Полный | ❌ Нет | ❌ Нет | 🔶 Опционально |
| **SSL** | ✅ Авто | ❌ Нет | ❌ Нет | 🔶 Ручная |
| **Production Ready** | ✅ Да | ❌ Нет | ❌ Нет | ✅ Да |
| **Сложность настройки** | Средняя | Простая | Очень простая | Высокая |
| **Производительность** | Высокая | Средняя | Низкая | Максимальная |

---

## 🔄 МИГРАЦИЯ МЕЖДУ ВАРИАНТАМИ

### Development → Production
```bash
# Остановить dev версию
docker-compose -f docker-compose.dev.yml down

# Добавить в .env настройки мониторинга
echo "GRAFANA_PASSWORD=TErmokit2024CDN!" >> .env

# Запустить production
docker-compose up -d
```

### Production → Native
```bash
# Экспорт настроек
./docker-manage.sh backup

# Остановка Docker версии
docker-compose down

# Native установка
make install BACKUP=docker-backup-$(date +%Y%m%d)
```

### Local → Development
```bash
# Настроить .env для внешнего сервера
nano .env  # добавить BITRIX_SERVER_* параметры

# Перезапуск с dev конфигурацией
docker-compose -f docker-compose.local.yml down
docker-compose -f docker-compose.dev.yml up -d
```