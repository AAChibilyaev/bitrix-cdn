# 🎯 МОНИТОРИНГ CDN - БЫСТРЫЙ СТАРТ

## ✅ УЖЕ РАБОТАЕТ

**5 систем запущены:**
- 📊 Grafana - http://localhost:3000
- 💚 Netdata - http://localhost:19999
- 🟢 Uptime Kuma - http://localhost:3001
- 📈 Prometheus - http://localhost:9090
- 🔔 Alertmanager - http://localhost:9093

---

## 🚀 ЗАПУСК

```bash
./AUTO_SETUP.sh
```

---

## 📊 ЧТО СМОТРЕТЬ

### 1. NETDATA (real-time)
http://localhost:19999
- Обновление каждую секунду
- 1000+ метрик
- Самый красивый интерфейс

### 2. GRAFANA (дашборды)
http://localhost:3000/d/cdn-complete
- Логин: admin / admin
- 5 дашбордов
- История за 15 дней

### 3. UPTIME KUMA (uptime)
http://localhost:3001
- Проверки доступности
- Уведомления

---

## 🔔 TELEGRAM АЛЕРТЫ

1. Создайте бота: @BotFather → /newbot
2. Получите Chat ID
3. Добавьте в .env:
```bash
TELEGRAM_BOT_TOKEN=ваш_токен
TELEGRAM_CHAT_ID=ваш_chat_id
```
4. Перезапустите:
```bash
sudo docker compose restart alertmanager
```

---

## 📈 GRAFANA ДАШБОРДЫ

1. **CDN Bitrix - Полный мониторинг** (главный)
   http://localhost:3000/d/cdn-complete

2. **CDN - Алерты**
   http://localhost:3000/d/cdn-alerts

3. **CDN - Производительность**
   http://localhost:3000/d/cdn-performance

4. **WebP Конвертер - Очередь**
   http://localhost:3000/d/webp-queue

---

## ⚙️ КОМАНДЫ

```bash
# Статус
sudo docker compose ps | grep -E "(netdata|uptime|alert|grafana|prometheus)"

# Перезапуск
sudo docker compose restart netdata uptime-kuma alertmanager grafana prometheus

# Логи
sudo docker compose logs -f alertmanager
```

---

**Подробно:** GRAFANA_DASHBOARDS.md, MONITORING_SYSTEMS.md
