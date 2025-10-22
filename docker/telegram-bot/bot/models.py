#!/usr/bin/env python3
"""
Строгие типы для Telegram бота (TypeScript-подобный подход)
"""

from typing import Dict, List, Optional, Union, Any, Literal
from dataclasses import dataclass
from enum import Enum
from pydantic import BaseModel, Field

# Базовые типы
ChatId = int
UserId = int
ServiceName = str
ContainerName = str
MetricName = str

# Статусы
ContainerStatus = Literal["running", "stopped", "paused", "restarting", "exited", "dead"]
HealthStatus = Literal["healthy", "unhealthy", "starting", "unknown"]
AlertSeverity = Literal["critical", "warning", "info"]
NotificationType = Literal["alert", "metric", "critical", "info"]

# Конфигурация
@dataclass
class TelegramConfig:
    token: str
    allowed_users: List[UserId]
    allowed_groups: List[ChatId]
    admin_users: List[UserId]

@dataclass
class PrometheusConfig:
    url: str
    timeout: int = 10

@dataclass
class DockerConfig:
    socket: str
    timeout: int = 30

@dataclass
class OpenAIConfig:
    api_key: str
    model: str
    max_tokens: int = 2000
    temperature: float = 0.7

@dataclass
class AlertManagerConfig:
    url: str
    timeout: int = 10

@dataclass
class NotificationConfig:
    enabled: bool
    check_interval: int
    critical_only: bool

@dataclass
class ServiceConfig:
    name: ServiceName
    container: ContainerName
    health_url: Optional[str] = None
    metrics_port: Optional[int] = None

@dataclass
class AppConfig:
    telegram: TelegramConfig
    prometheus: PrometheusConfig
    docker: DockerConfig
    openai: OpenAIConfig
    alertmanager: AlertManagerConfig
    notifications: NotificationConfig
    services: List[ServiceConfig]

# Данные контейнеров
@dataclass
class ContainerInfo:
    name: ContainerName
    status: ContainerStatus
    health: Optional[HealthStatus]
    image: str
    created: str
    ports: List[str]
    running: bool

# Health check данные
@dataclass
class HealthCheckResult:
    healthy: bool
    status: str
    response_time: Optional[int] = None
    status_code: Optional[int] = None
    error: Optional[str] = None

# Метрики
@dataclass
class NginxMetrics:
    requests_per_min: Optional[float]
    active_connections: Optional[int]
    cache_hit_rate: Optional[float]
    upstream_response_time: Optional[float]
    memory_usage: Optional[str]

@dataclass
class RedisMetrics:
    memory_used: Optional[str]
    keys_count: Optional[int]
    hit_rate: Optional[float]
    miss_rate: Optional[float]
    connected_clients: Optional[int]
    ops_per_sec: Optional[float]

@dataclass
class WebPMetrics:
    files_processed: Optional[int]
    files_failed: Optional[int]
    queue_size: Optional[int]
    processing_time: Optional[float]
    memory_usage: Optional[str]

@dataclass
class SystemMetrics:
    cpu_usage: Optional[float]
    memory_usage: Optional[str]
    disk_usage: Optional[str]
    load_average: Optional[float]
    network_tx: Optional[float]
    network_rx: Optional[float]

@dataclass
class AllMetrics:
    nginx: NginxMetrics
    redis: RedisMetrics
    webp: WebPMetrics
    system: SystemMetrics

# Алерты
@dataclass
class Alert:
    name: str
    status: str
    severity: AlertSeverity
    description: str
    summary: str
    starts_at: str
    updated_at: str

# Уведомления
@dataclass
class NotificationIssue:
    type: str
    severity: AlertSeverity
    service: ServiceName
    message: str

# AI анализ - Pydantic модели для Structured Outputs
class AISystemAnalysis(BaseModel):
    """Типизированный результат AI анализа системы"""
    status: Literal["healthy", "warning", "critical"]
    overall_health_score: int = Field(ge=0, le=100, description="Общая оценка здоровья системы от 0 до 100")
    problems: List[str] = Field(default_factory=list, description="Список выявленных проблем")
    recommendations: List[str] = Field(default_factory=list, description="Рекомендации по улучшению")
    forecast: Optional[str] = Field(None, description="Прогноз развития ситуации")
    
class AITrendAnalysis(BaseModel):
    """Анализ трендов производительности"""
    trend_direction: Literal["increasing", "decreasing", "stable"]
    predicted_issues: List[str] = Field(default_factory=list, description="Предсказанные проблемы")
    optimization_suggestions: List[str] = Field(default_factory=list, description="Предложения по оптимизации")
    confidence_score: int = Field(ge=0, le=100, description="Уверенность в прогнозе от 0 до 100")
    
class AIRecommendation(BaseModel):
    """Рекомендация по оптимизации"""
    priority: Literal["low", "medium", "high", "critical"]
    category: Literal["performance", "security", "reliability", "scalability"]
    title: str
    description: str
    implementation_steps: List[str] = Field(default_factory=list)
    estimated_impact: str

# Обратная совместимость - старый dataclass
@dataclass
class AIAnalysisResult:
    status: str
    problems: List[str]
    recommendations: List[str]
    performance_score: Optional[int]
    forecast: Optional[str]

# Кеш статистика
@dataclass
class RedisCacheStats:
    memory: str
    keys: str
    hit_rate: str

@dataclass
class NginxCacheStats:
    cache_size: str
    files: str

@dataclass
class CacheStatistics:
    redis: RedisCacheStats
    nginx: NginxCacheStats

# Результаты команд
@dataclass
class CommandResult:
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

# Пользовательские данные
@dataclass
class UserSession:
    user_id: UserId
    chat_id: ChatId
    is_admin: bool
    subscribed: bool
    last_activity: str

# API ответы
@dataclass
class APIResponse:
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    status_code: int = 200

# Типы для валидации
def validate_container_status(status: str) -> ContainerStatus:
    """Валидация статуса контейнера"""
    valid_statuses = ["running", "stopped", "paused", "restarting", "exited", "dead"]
    if status not in valid_statuses:
        raise ValueError(f"Invalid container status: {status}")
    return status

def validate_health_status(status: str) -> HealthStatus:
    """Валидация статуса здоровья"""
    valid_statuses = ["healthy", "unhealthy", "starting", "unknown"]
    if status not in valid_statuses:
        raise ValueError(f"Invalid health status: {status}")
    return status

def validate_alert_severity(severity: str) -> AlertSeverity:
    """Валидация серьезности алерта"""
    valid_severities = ["critical", "warning", "info"]
    if severity not in valid_severities:
        raise ValueError(f"Invalid alert severity: {severity}")
    return severity
