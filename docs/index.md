---
layout: default
title: Документация
nav_order: 2
has_children: true
permalink: /docs/
---

# 📚 Документация Bitrix CDN Server

Полная техническая документация для высокопроизводительного CDN решения с автоматической WebP конвертацией.

## ⚠️ Ключевая особенность архитектуры

**Двустороннее SSHFS монтирование:**
- CDN монтирует оригиналы с Битрикс (read-only)
- Битрикс монтирует resize_cache с CDN (read-write)
- resize_cache физически хранится на CDN сервере!

## 🎯 Разделы документации

### 🏗️ Архитектура и дизайн

| Документ | Описание |
|----------|----------|
| [Docker архитектура](./DOCKER_ARCHITECTURE.md) | Полная архитектура 11 контейнеров с диаграммами |
| [Сетевые потоки](./NETWORK_FLOWS.md) | Схемы сетевого взаимодействия и маппинг портов |
| [Файловая система](./VOLUMES_FILESYSTEM.md) | Docker volumes и стратегии резервного копирования |
| [Архитектура (legacy)](./ARCHITECTURE.md) | Базовая архитектура системы |

### 🚀 Установка и развертывание

| Документ | Описание |
|----------|----------|
| [Руководство по установке](./INSTALL.md) | Пошаговая инструкция установки |
| [Варианты деплоя](./DEPLOYMENT_VARIANTS.md) | Docker, Native, Kubernetes варианты |
| [Настройка Bitrix](./BITRIX_SETUP.md) | Интеграция с Битрикс сервером |
| [Настройка монтирования](./BITRIX_MOUNT_SETUP.md) | Двустороннее SSHFS монтирование |
| [CI/CD Pipeline](./CI_CD_PIPELINE.md) | GitHub Actions и автоматизация |

### 📊 Мониторинг и производительность

| Документ | Описание |
|----------|----------|
| [Метрики и алерты](./MONITORING_METRICS.md) | Prometheus/Grafana мониторинг |
| [Производительность](./PERFORMANCE_SCALING.md) | Benchmarks и масштабирование |
| [Мониторинг (legacy)](./MONITORING.md) | Базовый мониторинг |
| [Performance (legacy)](./PERFORMANCE.md) | Оптимизация производительности |

### 🔄 Процессы и операции

| Документ | Описание |
|----------|----------|
| [Обработка данных](./DATA_PROCESSING_FLOWS.md) | Потоки WebP конвертации |
| [Операционное управление](./OPERATIONAL_MANAGEMENT.md) | SLA и процедуры обслуживания |
| [Потоки данных (legacy)](./DATA_FLOW.md) | Базовые потоки данных |
| [Прогресс разработки](./DEVELOPMENT_PROGRESS.md) | Статус и roadmap |

### 🔒 Безопасность и оптимизация

| Документ | Описание |
|----------|----------|
| [Безопасность](./SECURITY_OPTIMIZATION.md) | Защита контейнеров и best practices |
| [Troubleshooting](./TROUBLESHOOTING.md) | Решение типовых проблем |
| [NGINX для Bitrix](./BITRIX_SERVER_NGINX.md) | Конфигурация NGINX на Битрикс |

---

## 🎨 Визуальные диаграммы

Документация содержит **30+ интерактивных Mermaid диаграмм**:

- 🏗️ **Архитектурные схемы** - Docker контейнеры и зависимости
- 🌐 **Сетевые диаграммы** - Потоки данных и коммуникация
- 📊 **Мониторинг** - Метрики, алерты и дашборды
- 🔄 **Процессы** - CI/CD, конвертация, кеширование
- 🔒 **Безопасность** - Защита и изоляция

---

## 🚀 С чего начать?

### Для быстрого старта:
1. [Руководство по установке](./INSTALL.md) - установка за 5 минут
2. [Docker архитектура](./DOCKER_ARCHITECTURE.md) - понимание системы
3. [Настройка Bitrix](./BITRIX_SETUP.md) - интеграция с сайтом

### Для разработчиков:
1. [CI/CD Pipeline](./CI_CD_PIPELINE.md) - автоматизация деплоя
2. [Варианты деплоя](./DEPLOYMENT_VARIANTS.md) - выбор стратегии
3. [Обработка данных](./DATA_PROCESSING_FLOWS.md) - понимание процессов

### Для DevOps:
1. [Метрики и алерты](./MONITORING_METRICS.md) - настройка мониторинга
2. [Операционное управление](./OPERATIONAL_MANAGEMENT.md) - поддержка системы
3. [Troubleshooting](./TROUBLESHOOTING.md) - решение проблем

---

## 📖 Формат документации

Каждый документ содержит:
- **Оглавление** для быстрой навигации
- **Визуальные схемы** в формате Mermaid
- **Примеры кода** с подсветкой синтаксиса
- **Практические примеры** использования
- **Ссылки** на связанные документы

---

## 🔗 Полезные ссылки

- [GitHub Repository](https://github.com/AAChibilyaev/bitrix-cdn)
- [Issues & Support](https://github.com/AAChibilyaev/bitrix-cdn/issues)
- [Releases](https://github.com/AAChibilyaev/bitrix-cdn/releases)
- [Главная страница](../)

---

## 📝 Обратная связь

Нашли ошибку или есть предложения по улучшению документации?

- 🐛 [Создайте Issue](https://github.com/AAChibilyaev/bitrix-cdn/issues/new)
- 📧 [Напишите автору](mailto:info@aachibilyaev.com)
- 🔀 [Отправьте Pull Request](https://github.com/AAChibilyaev/bitrix-cdn/pulls)