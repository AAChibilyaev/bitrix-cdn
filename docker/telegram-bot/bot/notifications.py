#!/usr/bin/env python3
"""
Служба проактивных уведомлений для Telegram бота
"""

import asyncio
import logging
from typing import Set, Dict, Any, List
from prometheus_client import PrometheusClient
from docker_client import DockerClient
from alerts import AlertsClient
from models import AppConfig

logger = logging.getLogger(__name__)

class NotificationService:
    """Служба проактивных уведомлений"""

    def __init__(self, bot, config: AppConfig):
        self.bot = bot
        self.config = config
        self.prometheus = PrometheusClient(config)
        self.docker = DockerClient(config)
        self.alerts = AlertsClient(config)

        # Подписчики на уведомления
        self.subscribers: Set[int] = set()

        # Настройки уведомлений
        self.notifications_config = config.notifications
        self.enabled = self.notifications_config.enabled
        self.check_interval = self.notifications_config.check_interval
        self.critical_only = self.notifications_config.critical_only
        
        logger.info(f"Notification service initialized: enabled={self.enabled}, interval={self.check_interval}s")
    
    async def start(self):
        """Запуск службы уведомлений"""
        if not self.enabled:
            logger.info("Notification service disabled")
            return
        
        logger.info("Starting notification service...")
        
        while True:
            try:
                await self._check_and_notify()
            except Exception as e:
                logger.error(f"Error in notification service: {e}")
            
            await asyncio.sleep(self.check_interval)
    
    async def _check_and_notify(self):
        """Проверка состояния системы и отправка уведомлений"""
        if not self.subscribers:
            return
        
        try:
            # Проверка алертов из AlertManager
            active_alerts = await self.alerts.get_active_alerts()
            if active_alerts:
                await self._send_alerts(active_alerts)
            
            # Проверка критических проблем
            critical_issues = await self._check_critical_issues()
            if critical_issues:
                await self._send_critical_issues(critical_issues)
            
            # Проверка метрик (если не только критические)
            if not self.critical_only:
                metric_issues = await self._check_metric_issues()
                if metric_issues:
                    await self._send_metric_issues(metric_issues)
        
        except Exception as e:
            logger.error(f"Error checking notifications: {e}")
    
    async def _check_critical_issues(self) -> List[Dict[str, Any]]:
        """Проверка критических проблем"""
        issues = []
        
        try:
            # Проверяем статус контейнеров
            containers = await self.docker.get_containers_status()
            
            for container in containers:
                if container['status'] != 'running':
                    issues.append({
                        'type': 'container_down',
                        'severity': 'critical',
                        'service': container['name'],
                        'message': f"Контейнер {container['name']} не работает: {container['status']}"
                    })
                elif container.get('health') and container['health'] not in ['healthy', 'starting']:
                    issues.append({
                        'type': 'container_unhealthy',
                        'severity': 'warning',
                        'service': container['name'],
                        'message': f"Контейнер {container['name']} нездоров: {container['health']}"
                    })
            
            # Проверяем health checks
            health_checks = await self.docker.get_health_checks()
            
            for service, status in health_checks.items():
                if not status['healthy']:
                    severity = 'critical' if service in ['nginx', 'redis'] else 'warning'
                    issues.append({
                        'type': 'health_check_failed',
                        'severity': severity,
                        'service': service,
                        'message': f"Health check {service} не прошел: {status['status']}"
                    })
        
        except Exception as e:
            logger.error(f"Error checking critical issues: {e}")
            issues.append({
                'type': 'monitoring_error',
                'severity': 'warning',
                'service': 'notification_service',
                'message': f"Ошибка мониторинга: {e}"
            })
        
        return issues
    
    async def _check_metric_issues(self) -> List[Dict[str, Any]]:
        """Проверка проблем с метриками"""
        issues = []
        
        try:
            # Получаем метрики
            metrics = await self.prometheus.get_all_metrics()
            
            # Проверяем Redis память
            if metrics.get('redis', {}).get('memory_used'):
                memory_str = metrics['redis']['memory_used']
                if 'GB' in memory_str:
                    memory_gb = float(memory_str.replace(' GB', ''))
                    if memory_gb > 1.5:  # Больше 1.5GB
                        issues.append({
                            'type': 'high_memory_usage',
                            'severity': 'warning',
                            'service': 'redis',
                            'message': f"Высокое использование памяти Redis: {memory_str}"
                        })
            
            # Проверяем Nginx запросы
            if metrics.get('nginx', {}).get('requests_per_min'):
                requests = metrics['nginx']['requests_per_min']
                if isinstance(requests, (int, float)) and requests > 1000:
                    issues.append({
                        'type': 'high_request_rate',
                        'severity': 'info',
                        'service': 'nginx',
                        'message': f"Высокая нагрузка на Nginx: {requests} запросов/мин"
                    })
        
        except Exception as e:
            logger.error(f"Error checking metric issues: {e}")
        
        return issues
    
    async def _send_alerts(self, alerts: List[Dict[str, Any]]):
        """Отправка алертов подписчикам"""
        for alert in alerts:
            message = self._format_alert(alert)
            await self._send_to_subscribers(message)
    
    async def _send_critical_issues(self, issues: List[Dict[str, Any]]):
        """Отправка критических проблем"""
        for issue in issues:
            if issue['severity'] == 'critical':
                message = self._format_critical_issue(issue)
                await self._send_to_subscribers(message)
    
    async def _send_metric_issues(self, issues: List[Dict[str, Any]]):
        """Отправка проблем с метриками"""
        for issue in issues:
            message = self._format_metric_issue(issue)
            await self._send_to_subscribers(message)
    
    async def _send_to_subscribers(self, message: str):
        """Отправка сообщения всем подписчикам"""
        for chat_id in self.subscribers:
            try:
                await self.bot.send_message(chat_id=chat_id, text=message)
            except Exception as e:
                logger.error(f"Error sending message to {chat_id}: {e}")
    
    def _format_alert(self, alert: Dict[str, Any]) -> str:
        """Форматирование алерта"""
        severity_emoji = "🔴" if alert.get('severity') == 'critical' else "🟡"
        
        message = f"{severity_emoji} *ALERT*\n\n"
        message += f"*Сервис:* {alert.get('name', 'Unknown')}\n"
        message += f"*Статус:* {alert.get('status', 'Unknown')}\n"
        message += f"*Описание:* {alert.get('description', 'No description')}\n"
        
        if alert.get('severity'):
            message += f"*Приоритет:* {alert['severity']}\n"
        
        return message
    
    def _format_critical_issue(self, issue: Dict[str, Any]) -> str:
        """Форматирование критической проблемы"""
        message = "🚨 *КРИТИЧЕСКАЯ ПРОБЛЕМА*\n\n"
        message += f"*Тип:* {issue.get('type', 'Unknown')}\n"
        message += f"*Сервис:* {issue.get('service', 'Unknown')}\n"
        message += f"*Сообщение:* {issue.get('message', 'No message')}\n"
        message += f"*Приоритет:* {issue.get('severity', 'Unknown')}\n"
        
        return message
    
    def _format_metric_issue(self, issue: Dict[str, Any]) -> str:
        """Форматирование проблемы с метриками"""
        severity_emoji = "🟡" if issue.get('severity') == 'warning' else "ℹ️"
        
        message = f"{severity_emoji} *МЕТРИКА*\n\n"
        message += f"*Тип:* {issue.get('type', 'Unknown')}\n"
        message += f"*Сервис:* {issue.get('service', 'Unknown')}\n"
        message += f"*Сообщение:* {issue.get('message', 'No message')}\n"
        
        return message
    
    def subscribe(self, chat_id: int):
        """Подписка на уведомления"""
        self.subscribers.add(chat_id)
        logger.info(f"User {chat_id} subscribed to notifications")
    
    def unsubscribe(self, chat_id: int):
        """Отписка от уведомлений"""
        self.subscribers.discard(chat_id)
        logger.info(f"User {chat_id} unsubscribed from notifications")
    
    def is_subscribed(self, chat_id: int) -> bool:
        """Проверка подписки"""
        return chat_id in self.subscribers
    
    def get_subscribers_count(self) -> int:
        """Количество подписчиков"""
        return len(self.subscribers)
