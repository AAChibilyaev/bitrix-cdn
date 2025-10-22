#!/usr/bin/env python3
"""
Telegram Bot для мониторинга Bitrix CDN
Основной модуль запуска бота
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Добавляем текущую директорию в путь для импортов
sys.path.append(str(Path(__file__).parent))

from telegram.ext import Application, CommandHandler
from handlers import (
    start_command, help_command, status_command, nginx_command,
    redis_command, webp_command, prometheus_command, containers_command,
    health_command, cache_command, ssl_command, logs_command, metrics_command,
    restart_command, analyze_command, report_command, alerts_command,
    subscribe_command, unsubscribe_command, ask_command, code_command,
    debug_command, suggest_command, quick_command, ping_command,
    summary_command, tips_command, shortcuts_command, trends_command,
    compare_command, forecast_command, settings_command, help_advanced_command,
    init_clients, load_allowed_users
)
from notifications import NotificationService
from config_loader import load_config, validate_config
from utils import setup_logging

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    """Основная функция запуска бота"""
    try:
        # Загрузка конфигурации
        config = load_config()
        validate_config(config)
        setup_logging({})  # Используем базовое логирование
        
        # Initialize clients
        init_clients(config)
        load_allowed_users()
        
        logger.info("Запуск Telegram бота для мониторинга CDN...")
        
        # Создание приложения
        app = Application.builder().token(config.telegram.token).build()
        
        # Регистрация команд
        app.add_handler(CommandHandler("start", start_command))
        app.add_handler(CommandHandler("help", help_command))
        app.add_handler(CommandHandler("status", status_command))
        app.add_handler(CommandHandler("nginx", nginx_command))
        app.add_handler(CommandHandler("redis", redis_command))
        app.add_handler(CommandHandler("webp", webp_command))
        app.add_handler(CommandHandler("prometheus", prometheus_command))
        app.add_handler(CommandHandler("containers", containers_command))
        app.add_handler(CommandHandler("health", health_command))
        app.add_handler(CommandHandler("cache", cache_command))
        app.add_handler(CommandHandler("ssl", ssl_command))
        app.add_handler(CommandHandler("logs", logs_command))
        app.add_handler(CommandHandler("metrics", metrics_command))
        app.add_handler(CommandHandler("restart", restart_command))
        app.add_handler(CommandHandler("analyze", analyze_command))
        app.add_handler(CommandHandler("report", report_command))
        app.add_handler(CommandHandler("alerts", alerts_command))
        app.add_handler(CommandHandler("subscribe", subscribe_command))
        app.add_handler(CommandHandler("unsubscribe", unsubscribe_command))
        
        # Интерактивные команды
        app.add_handler(CommandHandler("ask", ask_command))
        app.add_handler(CommandHandler("code", code_command))
        app.add_handler(CommandHandler("debug", debug_command))
        app.add_handler(CommandHandler("suggest", suggest_command))
        
        # Удобные команды
        app.add_handler(CommandHandler("quick", quick_command))
        app.add_handler(CommandHandler("ping", ping_command))
        app.add_handler(CommandHandler("summary", summary_command))
        app.add_handler(CommandHandler("tips", tips_command))
        app.add_handler(CommandHandler("shortcuts", shortcuts_command))
        
        # Анализ трендов
        app.add_handler(CommandHandler("trends", trends_command))
        app.add_handler(CommandHandler("compare", compare_command))
        app.add_handler(CommandHandler("forecast", forecast_command))
        
        # Дополнительные команды
        app.add_handler(CommandHandler("settings", settings_command))
        app.add_handler(CommandHandler("help_advanced", help_advanced_command))
        
        # Create notification service
        notification_service = NotificationService(app.bot, config)

        logger.info("Бот готов к работе!")

        # Start notification service in background
        # Note: NotificationService будет запущен в фоновом режиме во время работы бота
        # используя существующий event loop от telegram bot

        # Запуск бота
        app.run_polling()
        
    except Exception as e:
        logger.error(f"Ошибка запуска бота: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
