#!/usr/bin/env python3
"""
Продвинутая система мониторинга
"""

import asyncio
import time
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
from models import (
    AppConfig, ContainerInfo, HealthCheckResult, AllMetrics,
    Alert, AlertSeverity, NotificationIssue
)

logger = logging.getLogger(__name__)

class MetricType(Enum):
    """Типы метрик"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"

@dataclass
class MetricThreshold:
    """Пороговые значения для метрик"""
    metric_name: str
    warning_threshold: float
    critical_threshold: float
    unit: str = ""
    description: str = ""

@dataclass
class MonitoringRule:
    """Правило мониторинга"""
    name: str
    metric_name: str
    condition: str  # ">", "<", "==", "!="
    threshold: float
    severity: AlertSeverity
    description: str
    enabled: bool = True

class AdvancedMonitoring:
    """Продвинутая система мониторинга"""
    
    def __init__(self, config: AppConfig):
        self.config = config
        self.rules: List[MonitoringRule] = []
        self.metrics_history: Dict[str, List[Tuple[float, float]]] = {}  # metric_name -> [(timestamp, value)]
        self.alerts_history: List[Alert] = []
        self._setup_default_rules()
    
    def _setup_default_rules(self) -> None:
        """Настройка правил мониторинга по умолчанию"""
        default_rules = [
            MonitoringRule(
                name="high_memory_usage",
                metric_name="redis_memory_used_bytes",
                condition=">",
                threshold=1.5 * 1024**3,  # 1.5GB
                severity="warning",
                description="Высокое использование памяти Redis"
            ),
            MonitoringRule(
                name="critical_memory_usage",
                metric_name="redis_memory_used_bytes",
                condition=">",
                threshold=2.0 * 1024**3,  # 2GB
                severity="critical",
                description="Критическое использование памяти Redis"
            ),
            MonitoringRule(
                name="high_request_rate",
                metric_name="nginx_requests_per_second",
                condition=">",
                threshold=1000,
                severity="warning",
                description="Высокая нагрузка на Nginx"
            ),
            MonitoringRule(
                name="low_cache_hit_rate",
                metric_name="nginx_cache_hit_rate",
                condition="<",
                threshold=0.8,  # 80%
                severity="warning",
                description="Низкий hit rate кеша"
            ),
            MonitoringRule(
                name="container_down",
                metric_name="container_status",
                condition="!=",
                threshold=1,  # running = 1
                severity="critical",
                description="Контейнер не работает"
            )
        ]
        
        self.rules.extend(default_rules)
    
    async def check_metrics(self, metrics: AllMetrics) -> List[Alert]:
        """Проверка метрик на соответствие правилам"""
        alerts = []
        
        # Проверяем каждое правило
        for rule in self.rules:
            if not rule.enabled:
                continue
            
            try:
                # Получаем значение метрики
                metric_value = self._get_metric_value(metrics, rule.metric_name)
                if metric_value is None:
                    continue
                
                # Проверяем условие
                if self._evaluate_condition(metric_value, rule.condition, rule.threshold):
                    alert = Alert(
                        name=rule.name,
                        status="firing",
                        severity=rule.severity,
                        description=rule.description,
                        summary=f"{rule.description}: {metric_value}",
                        starts_at=str(int(time.time())),
                        updated_at=str(int(time.time()))
                    )
                    alerts.append(alert)
                    
                    # Сохраняем в историю
                    self.alerts_history.append(alert)
                    
            except Exception as e:
                logger.error(f"Ошибка проверки правила {rule.name}: {e}")
        
        return alerts
    
    def _get_metric_value(self, metrics: AllMetrics, metric_name: str) -> Optional[float]:
        """Получение значения метрики"""
        try:
            # Redis метрики
            if metric_name.startswith("redis_"):
                if hasattr(metrics.redis, metric_name.replace("redis_", "")):
                    value = getattr(metrics.redis, metric_name.replace("redis_", ""))
                    if isinstance(value, str) and "GB" in value:
                        return float(value.replace(" GB", "")) * 1024**3
                    elif isinstance(value, (int, float)):
                        return float(value)
            
            # Nginx метрики
            elif metric_name.startswith("nginx_"):
                if hasattr(metrics.nginx, metric_name.replace("nginx_", "")):
                    value = getattr(metrics.nginx, metric_name.replace("nginx_", ""))
                    if isinstance(value, (int, float)):
                        return float(value)
            
            # Системные метрики
            elif metric_name.startswith("system_"):
                if hasattr(metrics.system, metric_name.replace("system_", "")):
                    value = getattr(metrics.system, metric_name.replace("system_", ""))
                    if isinstance(value, (int, float)):
                        return float(value)
            
            return None
            
        except Exception as e:
            logger.error(f"Ошибка получения метрики {metric_name}: {e}")
            return None
    
    def _evaluate_condition(self, value: float, condition: str, threshold: float) -> bool:
        """Оценка условия"""
        if condition == ">":
            return value > threshold
        elif condition == "<":
            return value < threshold
        elif condition == "==":
            return value == threshold
        elif condition == "!=":
            return value != threshold
        elif condition == ">=":
            return value >= threshold
        elif condition == "<=":
            return value <= threshold
        else:
            return False
    
    async def analyze_trends(self, metric_name: str, time_window: int = 3600) -> Dict[str, Any]:
        """Анализ трендов метрики"""
        if metric_name not in self.metrics_history:
            return {"error": "No data available"}
        
        # Получаем данные за указанный период
        current_time = time.time()
        recent_data = [
            (timestamp, value) for timestamp, value in self.metrics_history[metric_name]
            if current_time - timestamp <= time_window
        ]
        
        if not recent_data:
            return {"error": "No recent data"}
        
        # Анализируем тренд
        values = [value for _, value in recent_data]
        timestamps = [timestamp for timestamp, _ in recent_data]
        
        # Простой линейный тренд
        if len(values) >= 2:
            slope = (values[-1] - values[0]) / (timestamps[-1] - timestamps[0])
            trend = "increasing" if slope > 0 else "decreasing" if slope < 0 else "stable"
        else:
            trend = "insufficient_data"
        
        return {
            "metric_name": metric_name,
            "data_points": len(recent_data),
            "current_value": values[-1],
            "min_value": min(values),
            "max_value": max(values),
            "avg_value": sum(values) / len(values),
            "trend": trend,
            "time_window": time_window
        }
    
    async def predict_issues(self, metrics: AllMetrics) -> List[str]:
        """Предсказание проблем на основе трендов"""
        predictions = []
        
        # Анализируем тренды ключевых метрик
        key_metrics = [
            "redis_memory_used_bytes",
            "nginx_requests_per_second",
            "nginx_cache_hit_rate"
        ]
        
        for metric_name in key_metrics:
            trend_analysis = await self.analyze_trends(metric_name, 1800)  # 30 минут
            
            if trend_analysis.get("trend") == "increasing":
                if metric_name == "redis_memory_used_bytes":
                    predictions.append("Возможно переполнение памяти Redis в ближайшее время")
                elif metric_name == "nginx_requests_per_second":
                    predictions.append("Ожидается увеличение нагрузки на Nginx")
                elif metric_name == "nginx_cache_hit_rate":
                    predictions.append("Снижение эффективности кеширования")
        
        return predictions
    
    def get_monitoring_stats(self) -> Dict[str, Any]:
        """Статистика мониторинга"""
        return {
            "rules_count": len(self.rules),
            "enabled_rules": len([r for r in self.rules if r.enabled]),
            "alerts_count": len(self.alerts_history),
            "metrics_tracked": len(self.metrics_history),
            "recent_alerts": len([
                alert for alert in self.alerts_history
                if time.time() - float(alert.starts_at) < 3600
            ])
        }
    
    async def cleanup_old_data(self, max_age: int = 86400) -> None:
        """Очистка старых данных"""
        current_time = time.time()
        
        # Очистка истории метрик
        for metric_name in list(self.metrics_history.keys()):
            self.metrics_history[metric_name] = [
                (timestamp, value) for timestamp, value in self.metrics_history[metric_name]
                if current_time - timestamp <= max_age
            ]
            if not self.metrics_history[metric_name]:
                del self.metrics_history[metric_name]
        
        # Очистка истории алертов
        self.alerts_history = [
            alert for alert in self.alerts_history
            if current_time - float(alert.starts_at) <= max_age
        ]
