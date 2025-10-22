#!/usr/bin/env python3
"""
Клиент для работы с AlertManager
"""

import logging
import aiohttp
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class AlertsClient:
    """Клиент для работы с AlertManager"""
    
    def __init__(self, config):
        self.config = config
        self.alertmanager_url = config.alertmanager.url
        logger.info(f"Alerts client initialized: {self.alertmanager_url}")
    
    async def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Получение активных алертов"""
        try:
            async with aiohttp.ClientSession() as session:
                # Получаем алерты через API v2
                url = f"{self.alertmanager_url}/api/v2/alerts"
                
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        alerts_data = await response.json()
                        
                        # Фильтруем только активные алерты
                        active_alerts = []
                        for alert in alerts_data:
                            if alert.get('status', {}).get('state') == 'active':
                                active_alerts.append({
                                    'name': alert.get('labels', {}).get('alertname', 'Unknown'),
                                    'status': alert.get('status', {}).get('state', 'Unknown'),
                                    'severity': alert.get('labels', {}).get('severity', 'warning'),
                                    'description': alert.get('annotations', {}).get('description', 'No description'),
                                    'summary': alert.get('annotations', {}).get('summary', 'No summary'),
                                    'starts_at': alert.get('startsAt', 'Unknown'),
                                    'updated_at': alert.get('updatedAt', 'Unknown')
                                })
                        
                        return active_alerts
                    else:
                        logger.warning(f"AlertManager API returned status {response.status}")
                        return []
        
        except Exception as e:
            logger.error(f"Error getting active alerts: {e}")
            return []
    
    async def get_alert_groups(self) -> List[Dict[str, Any]]:
        """Получение групп алертов"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.alertmanager_url}/api/v2/alerts/groups"
                
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        groups_data = await response.json()
                        return groups_data
                    else:
                        logger.warning(f"AlertManager groups API returned status {response.status}")
                        return []
        
        except Exception as e:
            logger.error(f"Error getting alert groups: {e}")
            return []
    
    async def get_silences(self) -> List[Dict[str, Any]]:
        """Получение активных silence"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.alertmanager_url}/api/v2/silences"
                
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        silences_data = await response.json()
                        return silences_data
                    else:
                        logger.warning(f"AlertManager silences API returned status {response.status}")
                        return []
        
        except Exception as e:
            logger.error(f"Error getting silences: {e}")
            return []
    
    async def create_silence(self, alert_name: str, duration: str = "1h") -> bool:
        """Создание silence для алерта"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.alertmanager_url}/api/v2/silences"
                
                silence_data = {
                    "matchers": [
                        {
                            "name": "alertname",
                            "value": alert_name,
                            "isRegex": False
                        }
                    ],
                    "startsAt": "2023-01-01T00:00:00.000Z",
                    "endsAt": "2023-01-01T01:00:00.000Z",
                    "createdBy": "telegram-bot",
                    "comment": f"Silence created by telegram bot for {duration}"
                }
                
                async with session.post(url, json=silence_data, timeout=10) as response:
                    if response.status == 200:
                        logger.info(f"Silence created for alert: {alert_name}")
                        return True
                    else:
                        logger.warning(f"Failed to create silence: {response.status}")
                        return False
        
        except Exception as e:
            logger.error(f"Error creating silence: {e}")
            return False
    
    async def get_alertmanager_status(self) -> Dict[str, Any]:
        """Получение статуса AlertManager"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.alertmanager_url}/api/v2/status"
                
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        status_data = await response.json()
                        return {
                            'status': 'ok',
                            'data': status_data
                        }
                    else:
                        return {
                            'status': 'error',
                            'error': f"HTTP {response.status}"
                        }
        
        except Exception as e:
            logger.error(f"Error getting AlertManager status: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    async def get_receivers(self) -> List[Dict[str, Any]]:
        """Получение списка receivers"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.alertmanager_url}/api/v2/receivers"
                
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        receivers_data = await response.json()
                        return receivers_data
                    else:
                        logger.warning(f"AlertManager receivers API returned status {response.status}")
                        return []
        
        except Exception as e:
            logger.error(f"Error getting receivers: {e}")
            return []
    
    async def test_webhook(self, webhook_url: str) -> bool:
        """Тестирование webhook"""
        try:
            async with aiohttp.ClientSession() as session:
                test_data = {
                    "alerts": [
                        {
                            "status": "firing",
                            "labels": {
                                "alertname": "TestAlert",
                                "severity": "warning"
                            },
                            "annotations": {
                                "description": "Test alert from telegram bot"
                            }
                        }
                    ]
                }
                
                async with session.post(webhook_url, json=test_data, timeout=10) as response:
                    if response.status in [200, 201, 202]:
                        logger.info(f"Webhook test successful: {webhook_url}")
                        return True
                    else:
                        logger.warning(f"Webhook test failed: {response.status}")
                        return False
        
        except Exception as e:
            logger.error(f"Error testing webhook: {e}")
            return False
