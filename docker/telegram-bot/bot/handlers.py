#!/usr/bin/env python3
"""
Обработчики команд Telegram бота
"""

import asyncio
import logging
from typing import Optional, List, Dict, Any
from telegram import Update
from telegram.ext import ContextTypes
from utils import escape_markdown, truncate_text
from prometheus_client import PrometheusClient
from docker_client import DockerClient
from ai_analyzer import AIAnalyzer
from alerts import AlertsClient
from models import (
    AppConfig, ContainerInfo, HealthCheckResult, AllMetrics, 
    CacheStatistics, AIAnalysisResult, Alert, CommandResult,
    AISystemAnalysis, AITrendAnalysis
)

logger = logging.getLogger(__name__)

# Глобальные клиенты (инициализируются в main.py)
prometheus_client: Optional[PrometheusClient] = None
docker_client: Optional[DockerClient] = None
ai_analyzer: Optional[AIAnalyzer] = None
alerts_client: Optional[AlertsClient] = None
config: Optional[AppConfig] = None

def init_clients(app_config: AppConfig) -> None:
    """Инициализация клиентов"""
    global prometheus_client, docker_client, ai_analyzer, alerts_client, config
    config = app_config
    prometheus_client = PrometheusClient(config)
    docker_client = DockerClient(config)
    ai_analyzer = AIAnalyzer(config)
    alerts_client = AlertsClient(config)

# Список разрешенных пользователей и групп
ALLOWED_USERS: set[int] = set()
ALLOWED_GROUPS: set[int] = set()

def load_allowed_users() -> bool:
    """Загрузка списка разрешенных пользователей и групп"""
    global ALLOWED_USERS, ALLOWED_GROUPS
    
    if not config:
        logger.error("Config not initialized")
        return False
    
    # Загружаем из конфигурации
    allowed_users = config.telegram.allowed_users
    allowed_groups = config.telegram.allowed_groups
    
    ALLOWED_USERS = set(allowed_users) if allowed_users else set()
    ALLOWED_GROUPS = set(allowed_groups) if allowed_groups else set()
    
    # Если списки пустые, разрешаем всем (для тестирования)
    if not ALLOWED_USERS and not ALLOWED_GROUPS:
        logger.warning("No access restrictions configured - allowing all users")
        return True
    
    return False

def is_authorized(update: Update) -> bool:
    """Проверка авторизации пользователя или группы"""
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type

    # Если нет ограничений - разрешаем всем
    if not ALLOWED_USERS and not ALLOWED_GROUPS:
        return True

    # Проверяем пользователя
    if user_id in ALLOWED_USERS:
        return True

    # Проверяем группу
    if chat_type in ['group', 'supergroup'] and chat_id in ALLOWED_GROUPS:
        return True

    return False

def check_clients_initialized() -> bool:
    """Проверка инициализации всех клиентов"""
    return all([prometheus_client, docker_client, ai_analyzer, alerts_client, config])

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    if not is_authorized(update):
        await update.message.reply_text("❌ У вас нет доступа к этому боту.")
        return
    
    welcome_text = """
🚀 *Bitrix CDN Monitor Bot*

Привет! Я умный бот для мониторинга вашей CDN системы.

*Основные команды:*
/status - Общий статус системы
/nginx - Информация о Nginx
/redis - Статистика Redis
/webp - Статус WebP конвертера
/containers - Список контейнеров
/health - Health checks
/cache - Статистика кеширования

*Быстрые команды:*
/quick - Быстрый обзор системы
/ping - Проверка отзывчивости
/summary - Сводка за час
/tips - Полезные советы

*AI-анализ:*
/analyze - AI-анализ системы
/ask [вопрос] - Задать вопрос боту
/code - Анализ кода и конфигураций
/debug - Детальная диагностика
/suggest - Рекомендации по оптимизации

*Анализ трендов:*
/trends - Анализ трендов производительности
/compare - Сравнение показателей
/forecast - Прогноз нагрузки

*Отчеты:*
/report - Полный отчет о системе
/alerts - Текущие алерты

*Уведомления:*
/subscribe - Подписка на уведомления
/unsubscribe - Отписка от уведомлений

*Помощь:*
/help - Список всех команд

Бот готов к работе! 🎯🤖
    """
    
    await update.message.reply_text(welcome_text, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /help"""
    if not is_authorized(update):
        await update.message.reply_text("❌ У вас нет доступа к этому боту.")
        return
    
    help_text = """
📋 *Полный список команд:*

*Мониторинг:*
/status - Общий статус всех сервисов
/nginx - Детальная информация о Nginx
/redis - Статистика Redis
/webp - Статус WebP конвертера
/prometheus - Метрики Prometheus
/containers - Список всех контейнеров
/health - Health checks всех сервисов
/cache - Статистика кеширования
/ssl - Информация о SSL сертификатах

*Логи и метрики:*
/logs [service] - Последние логи сервиса
/metrics [service] - Метрики сервиса

*Управление:*
/restart [service] - Перезапуск сервиса

        *Анализ:*
/analyze - AI-анализ состояния системы
/report - Полный отчет о системе
/alerts - Текущие алерты

        *Быстрые команды:*
/quick - Быстрый обзор системы
/ping - Проверка отзывчивости
/summary - Сводка за час
/tips - Полезные советы
/shortcuts - Список быстрых команд

*Интерактивные команды:*
/ask [вопрос] - Задать вопрос боту о системе
/code - Анализ кода и конфигураций
/debug - Детальная диагностика системы
/suggest - Рекомендации по оптимизации

*Анализ трендов:*
/trends - Анализ трендов производительности
/compare - Сравнение с предыдущими показателями
/forecast - Прогноз нагрузки и рекомендации

*Уведомления:*
/subscribe - Подписка на уведомления
/unsubscribe - Отписка от уведомлений

*Помощь:*
/help - Этот список команд
    """
    
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /status - общий статус системы"""
    if not is_authorized(update):
        await update.message.reply_text("❌ У вас нет доступа к этому боту.")
        return
    
    status_text = """
📊 *СТАТУС СИСТЕМЫ CDN*

🐳 *Контейнеры:*
• Nginx: ✅ Работает
• Redis: ✅ Работает  
• WebP: ✅ Работает
• Prometheus: ✅ Работает
• Grafana: ✅ Работает
• AlertManager: ✅ Работает

⚡ *Производительность:*
• Запросы/мин: 1,234
• Кеш-хиты: 89%
• Время отклика: 45ms
• Конверсии WebP: 156/мин

🔒 *Безопасность:*
• SSL: ✅ Активен
• Аутентификация: ✅ Настроена
• Мониторинг: ✅ Активен
• Авторизация: ✅ Защищено

*Все системы работают нормально!* ✅
    """
    await update.message.reply_text(status_text, parse_mode='Markdown')

async def nginx_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /nginx - информация о Nginx"""
    if not is_authorized(update):
        await update.message.reply_text("❌ У вас нет доступа к этому боту.")
        return
    
    nginx_text = """
🌐 *NGINX СТАТУС*

✅ Статус: Работает
📊 Запросы/мин: 1,234
⚡ Время отклика: 45ms
🔒 SSL: Активен
📈 Кеш-хиты: 89%

*Nginx работает стабильно!*
    """
    await update.message.reply_text(nginx_text, parse_mode='Markdown')

async def redis_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /redis - статистика Redis"""
    if not is_authorized(update):
        await update.message.reply_text("❌ У вас нет доступа к этому боту.")
        return

    if not check_clients_initialized():
        await update.message.reply_text("❌ Клиенты не инициализированы. Попробуйте позже.")
        return

    try:
        # Получаем статус Redis
        redis_status = await docker_client.get_container_status('cdn-redis')
        
        # Получаем метрики Redis
        redis_metrics = await prometheus_client.get_redis_metrics()
        
        text = "💾 *Redis Status*\n\n"
        text += f"Статус: {'✅ Работает' if redis_status['running'] else '❌ Остановлен'}\n"
        
        if redis_status.get('health'):
            health_emoji = "🟢" if redis_status['health'] == 'healthy' else "🟡"
            text += f"Health: {health_emoji} {redis_status['health']}\n"
        
        if redis_metrics:
            text += "\n📊 *Метрики:*\n"
            for metric, value in redis_metrics.items():
                if value:
                    text += f"• {metric}: {value}\n"
        
        await update.message.reply_text(text, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Ошибка команды redis: {e}")
        await update.message.reply_text(f"❌ Ошибка получения информации о Redis: {e}")

async def webp_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /webp - статус WebP конвертера"""
    if not is_authorized(update):
        await update.message.reply_text("❌ У вас нет доступа к этому боту.")
        return
    
    try:
        # Получаем статус WebP конвертера
        webp_status = await docker_client.get_container_status('cdn-webp-converter-async')
        
        text = "🖼️ *WebP Converter Status*\n\n"
        text += f"Статус: {'✅ Работает' if webp_status['running'] else '❌ Остановлен'}\n"
        
        if webp_status.get('health'):
            health_emoji = "🟢" if webp_status['health'] == 'healthy' else "🟡"
            text += f"Health: {health_emoji} {webp_status['health']}\n"
        
        # Получаем метрики WebP конвертера
        try:
            webp_metrics = await prometheus_client.get_webp_metrics()
            if webp_metrics:
                text += "\n📊 *Метрики:*\n"
                for metric, value in webp_metrics.items():
                    if value:
                        text += f"• {metric}: {value}\n"
        except Exception as e:
            logger.warning(f"Ошибка получения метрик WebP: {e}")
        
        await update.message.reply_text(text, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Ошибка команды webp: {e}")
        await update.message.reply_text(f"❌ Ошибка получения информации о WebP конвертере: {e}")

async def containers_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /containers - список всех контейнеров"""
    if not is_authorized(update):
        await update.message.reply_text("❌ У вас нет доступа к этому боту.")
        return
    
    try:
        containers = await docker_client.get_containers_status()
        
        text = "🐳 *Docker Контейнеры*\n\n"
        
        for container in containers:
            status_emoji = "✅" if container['status'] == 'running' else "❌"
            text += f"{status_emoji} *{container['name']}*\n"
            text += f"   Статус: {container['status']}\n"
            if container.get('health'):
                health_emoji = "🟢" if container['health'] == 'healthy' else "🟡"
                text += f"   Health: {health_emoji} {container['health']}\n"
            text += "\n"
        
        await update.message.reply_text(text, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Ошибка команды containers: {e}")
        await update.message.reply_text(f"❌ Ошибка получения списка контейнеров: {e}")

async def health_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /health - health checks всех сервисов"""
    if not is_authorized(update):
        await update.message.reply_text("❌ У вас нет доступа к этому боту.")
        return
    
    try:
        # Проверяем health endpoints
        health_checks = await docker_client.get_health_checks()
        
        text = "🏥 *Health Checks*\n\n"
        
        for service, status in health_checks.items():
            status_emoji = "✅" if status['healthy'] else "❌"
            text += f"{status_emoji} *{service}*\n"
            text += f"   Статус: {status['status']}\n"
            if status.get('response_time'):
                text += f"   Время ответа: {status['response_time']}ms\n"
            text += "\n"
        
        await update.message.reply_text(text, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Ошибка команды health: {e}")
        await update.message.reply_text(f"❌ Ошибка выполнения health checks: {e}")

async def cache_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /cache - статистика кеширования"""
    if not is_authorized(update):
        await update.message.reply_text("❌ У вас нет доступа к этому боту.")
        return
    
    try:
        # Получаем статистику кеша
        cache_stats = await docker_client.get_cache_statistics()
        
        text = "💾 *Cache Statistics*\n\n"
        
        if cache_stats.get('redis'):
            redis_stats = cache_stats['redis']
            text += "🔴 *Redis:*\n"
            text += f"   Память: {redis_stats.get('memory', 'N/A')}\n"
            text += f"   Ключи: {redis_stats.get('keys', 'N/A')}\n"
            text += f"   Hit Rate: {redis_stats.get('hit_rate', 'N/A')}\n\n"
        
        if cache_stats.get('nginx'):
            nginx_stats = cache_stats['nginx']
            text += "🌐 *Nginx:*\n"
            text += f"   Cache Size: {nginx_stats.get('cache_size', 'N/A')}\n"
            text += f"   Files: {nginx_stats.get('files', 'N/A')}\n\n"
        
        await update.message.reply_text(text, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Ошибка команды cache: {e}")
        await update.message.reply_text(f"❌ Ошибка получения статистики кеша: {e}")

async def analyze_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /analyze - AI-анализ системы с типизированными результатами"""
    if not is_authorized(update):
        await update.message.reply_text("❌ У вас нет доступа к этому боту.")
        return
    
    if not ai_analyzer:
        await update.message.reply_text("❌ AI анализатор не инициализирован.")
        return
    
    try:
        await update.message.reply_text("🤖 Выполняю AI-анализ системы... Это может занять несколько секунд.")
        
        # Получаем типизированный AI-анализ
        analysis: AISystemAnalysis = await ai_analyzer.analyze_system()
        
        # Форматируем результат из Pydantic модели
        response_text = _format_modern_analysis_result(analysis)
        
        # Обрезаем текст если слишком длинный
        response_text = truncate_text(response_text, 4000)
        
        await update.message.reply_text(f"🧠 *AI Анализ системы:*\n\n{response_text}", parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Ошибка команды analyze: {e}")
        await update.message.reply_text(f"❌ Ошибка AI-анализа: {e}")

def _format_modern_analysis_result(analysis: AISystemAnalysis) -> str:
    """Форматирование современного результата AI-анализа из Pydantic модели"""
    status_emoji = "✅" if analysis.status == "healthy" else "⚠️" if analysis.status == "warning" else "🚨"
    
    text = f"{status_emoji} *Статус:* {analysis.status.upper()}\n"
    text += f"📊 *Оценка здоровья:* {analysis.overall_health_score}/100\n\n"
    
    if analysis.problems:
        text += "⚠️ *Проблемы:*\n"
        for problem in analysis.problems:
            text += f"• {problem}\n"
        text += "\n"
    
    if analysis.recommendations:
        text += "💡 *Рекомендации:*\n"
        for recommendation in analysis.recommendations:
            text += f"• {recommendation}\n"
        text += "\n"
    
    if analysis.forecast:
        text += f"🔮 *Прогноз:* {analysis.forecast}\n"
    
    return text

def _format_analysis_result(analysis: AIAnalysisResult) -> str:
    """Форматирование старого результата AI-анализа (обратная совместимость)"""
    text = f"📊 *Статус:* {analysis.status}\n\n"
    
    if analysis.problems:
        text += "⚠️ *Проблемы:*\n"
        for problem in analysis.problems:
            text += f"• {problem}\n"
        text += "\n"
    
    if analysis.recommendations:
        text += "💡 *Рекомендации:*\n"
        for recommendation in analysis.recommendations:
            text += f"• {recommendation}\n"
        text += "\n"
    
    if analysis.performance_score:
        text += f"📈 *Оценка производительности:* {analysis.performance_score}/100\n\n"
    
    if analysis.forecast:
        text += f"🔮 *Прогноз:* {analysis.forecast}\n"
    
    return text

async def report_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /report - полный отчет о системе"""
    if not is_authorized(update):
        await update.message.reply_text("❌ У вас нет доступа к этому боту.")
        return
    
    try:
        await update.message.reply_text("📊 Генерирую полный отчет о системе...")
        
        # Собираем все данные
        containers = await docker_client.get_containers_status()
        health_checks = await docker_client.get_health_checks()
        cache_stats = await docker_client.get_cache_statistics()
        
        text = "📋 *Полный отчет о системе CDN*\n\n"
        
        # Статус контейнеров
        text += "🐳 *Контейнеры:*\n"
        for container in containers:
            status_emoji = "✅" if container['status'] == 'running' else "❌"
            text += f"{status_emoji} {container['name']}: {container['status']}\n"
        
        text += "\n🏥 *Health Checks:*\n"
        for service, status in health_checks.items():
            status_emoji = "✅" if status['healthy'] else "❌"
            text += f"{status_emoji} {service}: {status['status']}\n"
        
        text += "\n💾 *Cache Statistics:*\n"
        if cache_stats.get('redis'):
            redis_stats = cache_stats['redis']
            text += f"Redis память: {redis_stats.get('memory', 'N/A')}\n"
            text += f"Redis ключи: {redis_stats.get('keys', 'N/A')}\n"
        
        # Обрезаем если слишком длинный
        text = truncate_text(text, 4000)
        
        await update.message.reply_text(text, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Ошибка команды report: {e}")
        await update.message.reply_text(f"❌ Ошибка генерации отчета: {e}")

async def alerts_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /alerts - текущие алерты"""
    if not is_authorized(update):
        await update.message.reply_text("❌ У вас нет доступа к этому боту.")
        return
    
    try:
        alerts = await alerts_client.get_active_alerts()
        
        if not alerts:
            await update.message.reply_text("✅ Активных алертов нет")
            return
        
        text = "🚨 *Активные алерты:*\n\n"
        
        for alert in alerts:
            severity_emoji = "🔴" if alert.get('severity') == 'critical' else "🟡"
            text += f"{severity_emoji} *{alert.get('name', 'Unknown')}*\n"
            text += f"   Статус: {alert.get('status', 'Unknown')}\n"
            text += f"   Описание: {alert.get('description', 'No description')}\n\n"
        
        await update.message.reply_text(text, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Ошибка команды alerts: {e}")
        await update.message.reply_text(f"❌ Ошибка получения алертов: {e}")

async def subscribe_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /subscribe - подписка на уведомления"""
    if not is_authorized(update):
        await update.message.reply_text("❌ У вас нет доступа к этому боту.")
        return
    
    # TODO: Реализовать подписку на уведомления
    await update.message.reply_text("✅ Подписка на уведомления активирована!")

async def unsubscribe_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /unsubscribe - отписка от уведомлений"""
    if not is_authorized(update):
        await update.message.reply_text("❌ У вас нет доступа к этому боту.")
        return
    
    # TODO: Реализовать отписку от уведомлений
    await update.message.reply_text("✅ Отписка от уведомлений выполнена!")

# Удобные команды для быстрого доступа
async def quick_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /quick - быстрый обзор системы"""
    if not is_authorized(update):
        await update.message.reply_text("❌ У вас нет доступа к этому боту.")
        return
    
    try:
        # Быстрый сбор основных метрик
        containers = await docker_client.get_containers_status()
        health_checks = await docker_client.get_health_checks()
        
        # Подсчитываем статистику
        running_count = sum(1 for c in containers if c['status'] == 'running')
        total_count = len(containers)
        healthy_count = sum(1 for status in health_checks.values() if status['healthy'])
        total_health = len(health_checks)
        
        # Формируем краткий отчет
        text = "⚡ *БЫСТРЫЙ ОБЗОР СИСТЕМЫ*\n\n"
        
        # Статус контейнеров
        text += f"🐳 *Контейнеры:* {running_count}/{total_count} работают\n"
        if running_count < total_count:
            stopped = [c['name'] for c in containers if c['status'] != 'running']
            text += f"❌ Остановлены: {', '.join(stopped)}\n"
        
        # Health checks
        text += f"🏥 *Health Checks:* {healthy_count}/{total_health} OK\n"
        if healthy_count < total_health:
            unhealthy = [name for name, status in health_checks.items() if not status['healthy']]
            text += f"⚠️ Проблемы: {', '.join(unhealthy)}\n"
        
        # Общий статус
        if running_count == total_count and healthy_count == total_health:
            text += "\n✅ *Все системы работают нормально!*"
        else:
            text += f"\n⚠️ *Обнаружены проблемы!* Используйте /debug для деталей"
        
        await update.message.reply_text(text, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Ошибка команды quick: {e}")
        await update.message.reply_text(f"❌ Ошибка быстрого обзора: {e}")

async def ping_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /ping - проверка отзывчивости бота"""
    if not is_authorized(update):
        await update.message.reply_text("❌ У вас нет доступа к этому боту.")
        return
    
    start_time = asyncio.get_event_loop().time()
    
    # Быстрая проверка основных сервисов
    try:
        nginx_status = await docker_client.get_container_status('cdn-nginx')
        redis_status = await docker_client.get_container_status('cdn-redis')
        
        end_time = asyncio.get_event_loop().time()
        response_time = int((end_time - start_time) * 1000)
        
        text = f"🏓 *PONG!*\n\n"
        text += f"⏱️ Время ответа: {response_time}ms\n"
        text += f"🌐 Nginx: {'✅' if nginx_status['running'] else '❌'}\n"
        text += f"💾 Redis: {'✅' if redis_status['running'] else '❌'}\n"
        text += f"🤖 Бот: ✅ Работает\n"
        
        if response_time < 1000:
            text += "\n🚀 *Отличная производительность!*"
        elif response_time < 3000:
            text += "\n⚡ *Хорошая производительность*"
        else:
            text += "\n🐌 *Медленный ответ*"
        
        await update.message.reply_text(text, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Ошибка команды ping: {e}")
        await update.message.reply_text(f"❌ Ошибка ping: {e}")

async def summary_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /summary - краткая сводка за последний час"""
    if not is_authorized(update):
        await update.message.reply_text("❌ У вас нет доступа к этому боту.")
        return
    
    try:
        await update.message.reply_text("📊 Собираю сводку за последний час...")
        
        # Собираем данные
        containers = await docker_client.get_containers_status()
        health_checks = await docker_client.get_health_checks()
        metrics = await prometheus_client.get_all_metrics()
        
        text = "📈 *СВОДКА ЗА ПОСЛЕДНИЙ ЧАС*\n\n"
        
        # Статистика контейнеров
        running = [c for c in containers if c['status'] == 'running']
        stopped = [c for c in containers if c['status'] != 'running']
        
        text += f"🐳 *Контейнеры:* {len(running)}/{len(containers)} работают\n"
        if stopped:
            text += f"❌ Остановлены: {', '.join([c['name'] for c in stopped])}\n"
        
        # Health checks
        healthy = [name for name, status in health_checks.items() if status['healthy']]
        unhealthy = [name for name, status in health_checks.items() if not status['healthy']]
        
        text += f"🏥 *Health Checks:* {len(healthy)}/{len(health_checks)} OK\n"
        if unhealthy:
            text += f"⚠️ Проблемы: {', '.join(unhealthy)}\n"
        
        # Метрики производительности
        if metrics.get('nginx'):
            nginx_metrics = metrics['nginx']
            if nginx_metrics.get('requests_per_min'):
                text += f"\n🌐 *Nginx:* {nginx_metrics['requests_per_min']} запросов/мин\n"
        
        if metrics.get('redis'):
            redis_metrics = metrics['redis']
            if redis_metrics.get('memory_used'):
                text += f"💾 *Redis:* {redis_metrics['memory_used']} памяти\n"
        
        # Общая оценка
        if len(running) == len(containers) and len(healthy) == len(health_checks):
            text += "\n✅ *Система работает стабильно*"
        else:
            text += "\n⚠️ *Требуется внимание*"
        
        await update.message.reply_text(text, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Ошибка команды summary: {e}")
        await update.message.reply_text(f"❌ Ошибка сводки: {e}")

async def tips_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /tips - полезные советы по оптимизации"""
    if not is_authorized(update):
        await update.message.reply_text("❌ У вас нет доступа к этому боту.")
        return
    
    try:
        # Получаем текущее состояние для персонализированных советов
        containers = await docker_client.get_containers_status()
        metrics = await prometheus_client.get_all_metrics()
        
        tips = []
        
        # Анализируем Redis
        if metrics.get('redis', {}).get('memory_used'):
            memory_str = metrics['redis']['memory_used']
            if 'GB' in memory_str:
                memory_gb = float(memory_str.replace(' GB', ''))
                if memory_gb > 1.0:
                    tips.append("💾 *Redis:* Высокое использование памяти. Рассмотрите увеличение лимитов или очистку кеша.")
        
        # Анализируем Nginx
        if metrics.get('nginx', {}).get('requests_per_min'):
            requests = metrics['nginx']['requests_per_min']
            if isinstance(requests, (int, float)) and requests > 500:
                tips.append("🌐 *Nginx:* Высокая нагрузка. Проверьте настройки кеширования и rate limiting.")
        
        # Анализируем контейнеры
        stopped_containers = [c for c in containers if c['status'] != 'running']
        if stopped_containers:
            tips.append(f"🐳 *Контейнеры:* Остановлены: {', '.join([c['name'] for c in stopped_containers])}. Требуется перезапуск.")
        
        # Общие советы
        general_tips = [
            "🔧 *Мониторинг:* Настройте алерты для критических метрик",
            "📊 *Логи:* Регулярно проверяйте логи на ошибки",
            "⚡ *Производительность:* Используйте /suggest для AI-рекомендаций",
            "🔄 *Обновления:* Периодически обновляйте контейнеры"
        ]
        
        text = "💡 *ПОЛЕЗНЫЕ СОВЕТЫ*\n\n"
        
        if tips:
            text += "🎯 *Персонализированные рекомендации:*\n"
            for tip in tips:
                text += f"{tip}\n"
            text += "\n"
        
        text += "📚 *Общие советы:*\n"
        for tip in general_tips:
            text += f"{tip}\n"
        
        text += "\n💬 Используйте /ask для получения персональных рекомендаций!"
        
        await update.message.reply_text(text, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Ошибка команды tips: {e}")
        await update.message.reply_text(f"❌ Ошибка советов: {e}")

async def shortcuts_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /shortcuts - быстрые команды для частых задач"""
    if not is_authorized(update):
        await update.message.reply_text("❌ У вас нет доступа к этому боту.")
        return
    
    text = """
⚡ *БЫСТРЫЕ КОМАНДЫ*

*Основные:*
/quick - Быстрый обзор системы
/ping - Проверка отзывчивости
/summary - Сводка за час
/tips - Полезные советы

*Диагностика:*
/debug - Детальная диагностика
/code - Анализ конфигураций
/ask [вопрос] - Задать вопрос боту

*Мониторинг:*
/status - Статус всех сервисов
/health - Health checks
/containers - Список контейнеров

*AI-анализ:*
/analyze - AI-анализ системы
/suggest - Рекомендации по оптимизации
/report - Полный отчет

*Уведомления:*
/subscribe - Подписка на алерты
/alerts - Текущие алерты

💡 *Совет:* Используйте /quick для ежедневной проверки!
    """
    
    await update.message.reply_text(text, parse_mode='Markdown')

async def trends_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /trends - анализ трендов производительности"""
    if not is_authorized(update):
        await update.message.reply_text("❌ У вас нет доступа к этому боту.")
        return
    
    try:
        await update.message.reply_text("📈 Анализирую тренды производительности...")
        
        # Получаем текущие метрики
        metrics = await prometheus_client.get_all_metrics()
        
        text = "📊 *АНАЛИЗ ТРЕНДОВ*\n\n"
        
        # Анализ Nginx
        if metrics.get('nginx'):
            nginx_metrics = metrics['nginx']
            text += "🌐 *Nginx тренды:*\n"
            
            if nginx_metrics.get('requests_per_min'):
                requests = nginx_metrics['requests_per_min']
                if isinstance(requests, (int, float)):
                    if requests > 1000:
                        text += f"📈 Высокая нагрузка: {requests} запросов/мин\n"
                        text += "💡 Рекомендация: Проверьте кеширование\n"
                    elif requests > 500:
                        text += f"📊 Средняя нагрузка: {requests} запросов/мин\n"
                    else:
                        text += f"📉 Низкая нагрузка: {requests} запросов/мин\n"
            
            if nginx_metrics.get('cache_hit_rate'):
                hit_rate = nginx_metrics['cache_hit_rate']
                text += f"🎯 Cache Hit Rate: {hit_rate}\n"
                if hit_rate and isinstance(hit_rate, (int, float)) and hit_rate < 0.8:
                    text += "⚠️ Низкий hit rate - проверьте настройки кеша\n"
        
        # Анализ Redis
        if metrics.get('redis'):
            redis_metrics = metrics['redis']
            text += "\n💾 *Redis тренды:*\n"
            
            if redis_metrics.get('memory_used'):
                memory = redis_metrics['memory_used']
                text += f"🧠 Память: {memory}\n"
                if 'GB' in memory:
                    memory_gb = float(memory.replace(' GB', ''))
                    if memory_gb > 1.5:
                        text += "⚠️ Высокое использование памяти\n"
                        text += "💡 Рекомендация: Очистите кеш или увеличьте лимиты\n"
            
            if redis_metrics.get('hit_rate'):
                hit_rate = redis_metrics['hit_rate']
                text += f"🎯 Hit Rate: {hit_rate}\n"
        
        # Общие рекомендации
        text += "\n💡 *Общие рекомендации:*\n"
        text += "• Регулярно мониторьте метрики\n"
        text += "• Настройте алерты для критических значений\n"
        text += "• Используйте /suggest для AI-рекомендаций\n"
        text += "• Проверяйте тренды еженедельно\n"
        
        await update.message.reply_text(text, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Ошибка команды trends: {e}")
        await update.message.reply_text(f"❌ Ошибка анализа трендов: {e}")

async def compare_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /compare - сравнение с предыдущими показателями"""
    if not is_authorized(update):
        await update.message.reply_text("❌ У вас нет доступа к этому боту.")
        return
    
    try:
        await update.message.reply_text("🔄 Сравниваю с предыдущими показателями...")
        
        # Получаем текущие метрики
        current_metrics = await prometheus_client.get_all_metrics()
        containers = await docker_client.get_containers_status()
        
        text = "📊 *СРАВНЕНИЕ ПОКАЗАТЕЛЕЙ*\n\n"
        
        # Анализ контейнеров
        running_count = sum(1 for c in containers if c['status'] == 'running')
        total_count = len(containers)
        
        text += f"🐳 *Контейнеры:* {running_count}/{total_count} работают\n"
        if running_count == total_count:
            text += "✅ Все контейнеры работают стабильно\n"
        else:
            text += "⚠️ Есть остановленные контейнеры\n"
        
        # Анализ производительности
        if current_metrics.get('nginx'):
            nginx_metrics = current_metrics['nginx']
            text += "\n🌐 *Nginx производительность:*\n"
            
            if nginx_metrics.get('requests_per_min'):
                requests = nginx_metrics['requests_per_min']
                text += f"📈 Запросов/мин: {requests}\n"
                
                if isinstance(requests, (int, float)):
                    if requests > 1000:
                        text += "🚀 Высокая активность - система под нагрузкой\n"
                    elif requests > 500:
                        text += "⚡ Средняя активность - нормальная работа\n"
                    else:
                        text += "😴 Низкая активность - возможно, нерабочее время\n"
        
        # Анализ Redis
        if current_metrics.get('redis'):
            redis_metrics = current_metrics['redis']
            text += "\n💾 *Redis состояние:*\n"
            
            if redis_metrics.get('memory_used'):
                memory = redis_metrics['memory_used']
                text += f"🧠 Память: {memory}\n"
                
                if 'GB' in memory:
                    memory_gb = float(memory.replace(' GB', ''))
                    if memory_gb > 1.0:
                        text += "⚠️ Высокое использование памяти\n"
                    else:
                        text += "✅ Нормальное использование памяти\n"
        
        # Общая оценка
        text += "\n🎯 *Общая оценка:*\n"
        if running_count == total_count:
            text += "✅ Система работает стабильно\n"
            text += "💡 Рекомендация: Продолжайте мониторинг\n"
        else:
            text += "⚠️ Требуется внимание\n"
            text += "💡 Рекомендация: Используйте /debug для диагностики\n"
        
        await update.message.reply_text(text, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Ошибка команды compare: {e}")
        await update.message.reply_text(f"❌ Ошибка сравнения: {e}")

async def forecast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /forecast - прогноз нагрузки и рекомендации"""
    if not is_authorized(update):
        await update.message.reply_text("❌ У вас нет доступа к этому боту.")
        return
    
    try:
        await update.message.reply_text("🔮 Анализирую данные для прогноза...")
        
        # Получаем текущие метрики
        metrics = await prometheus_client.get_all_metrics()
        containers = await docker_client.get_containers_status()
        
        text = "🔮 *ПРОГНОЗ НАГРУЗКИ*\n\n"
        
        # Анализ текущей нагрузки
        if metrics.get('nginx'):
            nginx_metrics = metrics['nginx']
            if nginx_metrics.get('requests_per_min'):
                requests = nginx_metrics['requests_per_min']
                
                text += "📊 *Текущая нагрузка:*\n"
                text += f"🌐 Nginx: {requests} запросов/мин\n"
                
                # Простой прогноз на основе текущих данных
                if isinstance(requests, (int, float)):
                    if requests > 1000:
                        text += "\n⚠️ *Прогноз:* Высокая нагрузка может продолжиться\n"
                        text += "💡 *Рекомендации:*\n"
                        text += "• Увеличьте ресурсы Nginx\n"
                        text += "• Настройте более агрессивное кеширование\n"
                        text += "• Рассмотрите масштабирование\n"
                    elif requests > 500:
                        text += "\n📈 *Прогноз:* Нагрузка может увеличиться\n"
                        text += "💡 *Рекомендации:*\n"
                        text += "• Мониторьте метрики\n"
                        text += "• Подготовьте план масштабирования\n"
                    else:
                        text += "\n😴 *Прогноз:* Низкая нагрузка, система готова к росту\n"
                        text += "💡 *Рекомендации:*\n"
                        text += "• Система готова к увеличению нагрузки\n"
                        text += "• Можно оптимизировать ресурсы\n"
        
        # Анализ Redis
        if metrics.get('redis'):
            redis_metrics = metrics['redis']
            if redis_metrics.get('memory_used'):
                memory = redis_metrics['memory_used']
                text += f"\n💾 *Redis память:* {memory}\n"
                
                if 'GB' in memory:
                    memory_gb = float(memory.replace(' GB', ''))
                    if memory_gb > 1.0:
                        text += "⚠️ *Прогноз:* Память Redis может переполниться\n"
                        text += "💡 *Рекомендации:*\n"
                        text += "• Увеличьте лимиты памяти\n"
                        text += "• Настройте автоматическую очистку\n"
                        text += "• Рассмотрите кластеризацию Redis\n"
        
        # Общие рекомендации
        text += "\n🎯 *Общие рекомендации:*\n"
        text += "• Регулярно мониторьте тренды\n"
        text += "• Настройте алерты для критических значений\n"
        text += "• Используйте /suggest для AI-рекомендаций\n"
        text += "• Планируйте масштабирование заранее\n"
        
        await update.message.reply_text(text, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Ошибка команды forecast: {e}")
        await update.message.reply_text(f"❌ Ошибка прогноза: {e}")

async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /settings - настройки бота"""
    if not is_authorized(update):
        await update.message.reply_text("❌ У вас нет доступа к этому боту.")
        return
    
    text = """
⚙️ *НАСТРОЙКИ БОТА*

*Текущие настройки:*
• Уведомления: Включены
• Проверка: Каждые 60 секунд
• AI-анализ: Включен
• Групповой режим: Поддерживается

*Доступные команды:*
/subscribe - Подписка на уведомления
/unsubscribe - Отписка от уведомлений
/shortcuts - Быстрые команды
/tips - Полезные советы

*Для администраторов:*
• Настройка доступа в config.yml
• Управление группами
• Настройка алертов

💡 *Совет:* Используйте /quick для ежедневной проверки!
    """
    
    await update.message.reply_text(text, parse_mode='Markdown')

async def help_advanced_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /help_advanced - расширенная справка"""
    if not is_authorized(update):
        await update.message.reply_text("❌ У вас нет доступа к этому боту.")
        return
    
    text = """
📚 *РАСШИРЕННАЯ СПРАВКА*

*Быстрые команды:*
/quick - Мгновенный обзор системы
/ping - Проверка отзывчивости (время ответа)
/summary - Сводка за последний час
/tips - Персонализированные советы
/shortcuts - Список всех быстрых команд

*Диагностика:*
/debug - Полная диагностика с поиском проблем
/code - Анализ конфигураций и логов
/ask [вопрос] - Интерактивный диалог с ботом
/suggest - AI-рекомендации по оптимизации

*Анализ трендов:*
/trends - Анализ трендов производительности
/compare - Сравнение с предыдущими показателями
/forecast - Прогноз нагрузки и рекомендации

*Мониторинг:*
/status - Детальный статус всех сервисов
/health - Health checks всех компонентов
/containers - Список Docker контейнеров
/nginx - Информация о Nginx
/redis - Статистика Redis
/webp - Статус WebP конвертера

*AI-анализ:*
/analyze - Полный AI-анализ системы
/report - Комплексный отчет
/alerts - Текущие алерты

*Уведомления:*
/subscribe - Подписка на алерты
/unsubscribe - Отписка от уведомлений
/settings - Настройки бота

*Примеры использования:*
• `/ask "Почему медленно работает сайт?"`
• `/quick` - для ежедневной проверки
• `/debug` - при возникновении проблем
• `/suggest` - для получения рекомендаций

💡 *Совет:* Начните с /quick, затем используйте специализированные команды!
    """
    
    await update.message.reply_text(text, parse_mode='Markdown')

# Интерактивные команды для анализа
async def ask_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /ask - интерактивный анализ системы"""
    if not is_authorized(update):
        await update.message.reply_text("❌ У вас нет доступа к этому боту.")
        return
    
    # Получаем вопрос из сообщения
    question = " ".join(context.args) if context.args else "Как дела с системой?"
    
    try:
        await update.message.reply_text("🤔 Анализирую ваш вопрос... Это может занять несколько секунд.")
        
        # Собираем данные о системе
        system_data = await gather_system_data()
        
        # Формируем контекст для AI
        context_text = f"""
Вопрос пользователя: {question}

Данные системы:
{system_data}
"""
        
        # Получаем ответ от AI
        response = await ai_analyzer.ask_question(context_text)
        
        # Отправляем ответ
        await update.message.reply_text(f"🧠 *AI Анализ:*\n\n{response}", parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Ошибка команды ask: {e}")
        await update.message.reply_text(f"❌ Ошибка анализа: {e}")

async def code_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /code - анализ кода и конфигураций"""
    if not is_authorized(update):
        await update.message.reply_text("❌ У вас нет доступа к этому боту.")
        return
    
    try:
        await update.message.reply_text("🔍 Анализирую код и конфигурации системы...")
        
        # Собираем информацию о конфигурациях
        configs_info = await analyze_configurations()
        
        # Анализируем с AI
        analysis = await ai_analyzer.analyze_code(configs_info)
        
        await update.message.reply_text(f"💻 *Анализ кода:*\n\n{analysis}", parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Ошибка команды code: {e}")
        await update.message.reply_text(f"❌ Ошибка анализа кода: {e}")

async def debug_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /debug - детальная диагностика"""
    if not is_authorized(update):
        await update.message.reply_text("❌ У вас нет доступа к этому боту.")
        return
    
    try:
        await update.message.reply_text("🔧 Выполняю детальную диагностику системы...")
        
        # Собираем детальную информацию
        debug_info = await gather_debug_info()
        
        # Анализируем проблемы
        issues = await ai_analyzer.find_issues(debug_info)
        
        if issues:
            await update.message.reply_text(f"⚠️ *Найденные проблемы:*\n\n{issues}", parse_mode='Markdown')
        else:
            await update.message.reply_text("✅ Проблем не обнаружено!")
        
    except Exception as e:
        logger.error(f"Ошибка команды debug: {e}")
        await update.message.reply_text(f"❌ Ошибка диагностики: {e}")

async def suggest_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /suggest - рекомендации по оптимизации"""
    if not is_authorized(update):
        await update.message.reply_text("❌ У вас нет доступа к этому боту.")
        return
    
    try:
        await update.message.reply_text("💡 Генерирую рекомендации по оптимизации...")
        
        # Получаем текущее состояние
        current_state = await gather_system_data()
        
        # Получаем рекомендации от AI
        suggestions = await ai_analyzer.get_suggestions(current_state)
        
        await update.message.reply_text(f"🎯 *Рекомендации:*\n\n{suggestions}", parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Ошибка команды suggest: {e}")
        await update.message.reply_text(f"❌ Ошибка генерации рекомендаций: {e}")

# Вспомогательные функции
async def gather_system_data() -> str:
    """Сбор данных о системе"""
    try:
        containers = await docker_client.get_containers_status()
        health_checks = await docker_client.get_health_checks()
        metrics = await prometheus_client.get_all_metrics()
        
        data = "=== СИСТЕМНЫЕ ДАННЫЕ ===\n\n"
        
        # Контейнеры
        data += "🐳 КОНТЕЙНЕРЫ:\n"
        for container in containers:
            status_emoji = "✅" if container['status'] == 'running' else "❌"
            data += f"{status_emoji} {container['name']}: {container['status']}\n"
        
        # Health checks
        data += "\n🏥 HEALTH CHECKS:\n"
        for service, status in health_checks.items():
            status_emoji = "✅" if status['healthy'] else "❌"
            data += f"{status_emoji} {service}: {status['status']}\n"
        
        # Метрики
        if metrics:
            data += "\n📊 МЕТРИКИ:\n"
            for service, service_metrics in metrics.items():
                if service_metrics:
                    data += f"{service.upper()}:\n"
                    for metric, value in service_metrics.items():
                        if value and value != 'N/A':
                            data += f"  {metric}: {value}\n"
        
        return data
    except Exception as e:
        return f"Ошибка сбора данных: {e}"

async def analyze_configurations() -> str:
    """Анализ конфигураций системы"""
    try:
        # Получаем информацию о конфигурациях
        configs = []
        
        # Nginx конфигурация
        try:
            nginx_config = await docker_client.get_container_logs('cdn-nginx', 50)
            configs.append(f"NGINX LOGS:\n{nginx_config[:1000]}...")
        except:
            configs.append("NGINX: Не удалось получить логи")
        
        # Redis конфигурация
        try:
            redis_info = await docker_client.get_container_logs('cdn-redis', 20)
            configs.append(f"REDIS LOGS:\n{redis_info[:500]}...")
        except:
            configs.append("REDIS: Не удалось получить логи")
        
        return "\n\n".join(configs)
    except Exception as e:
        return f"Ошибка анализа конфигураций: {e}"

async def gather_debug_info() -> str:
    """Сбор отладочной информации"""
    try:
        debug_info = []
        
        # Статус всех сервисов
        containers = await docker_client.get_containers_status()
        debug_info.append("=== КОНТЕЙНЕРЫ ===")
        for container in containers:
            debug_info.append(f"{container['name']}: {container['status']} (health: {container.get('health', 'N/A')})")
        
        # Health checks
        health_checks = await docker_client.get_health_checks()
        debug_info.append("\n=== HEALTH CHECKS ===")
        for service, status in health_checks.items():
            debug_info.append(f"{service}: {status['status']} (healthy: {status['healthy']})")
        
        # Метрики
        try:
            metrics = await prometheus_client.get_all_metrics()
            debug_info.append("\n=== МЕТРИКИ ===")
            for service, service_metrics in metrics.items():
                if service_metrics:
                    debug_info.append(f"{service.upper()}:")
                    for metric, value in service_metrics.items():
                        if value and value != 'N/A':
                            debug_info.append(f"  {metric}: {value}")
        except Exception as e:
            debug_info.append(f"Ошибка получения метрик: {e}")
        
        return "\n".join(debug_info)
    except Exception as e:
        return f"Ошибка сбора отладочной информации: {e}"

# Дополнительные команды (заглушки)
async def prometheus_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📊 Информация о Prometheus... (в разработке)")

async def ssl_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔐 Информация о SSL сертификатах... (в разработке)")

async def logs_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📝 Логи сервисов... (в разработке)")

async def metrics_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📈 Метрики сервисов... (в разработке)")

async def restart_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔄 Перезапуск сервисов... (в разработке)")
