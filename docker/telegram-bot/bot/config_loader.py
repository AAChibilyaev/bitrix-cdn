#!/usr/bin/env python3
"""
Загрузчик конфигурации с типизацией
"""

import os
import yaml
from typing import Dict, Any, List
from models import (
    AppConfig, TelegramConfig, PrometheusConfig, DockerConfig,
    OpenAIConfig, AlertManagerConfig, NotificationConfig, ServiceConfig
)

def load_config() -> AppConfig:
    """Загрузка и валидация конфигурации"""
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config.yml')
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            raw_config = yaml.safe_load(f)
        
        # Замена переменных окружения
        raw_config = _replace_env_vars(raw_config)
        
        # Валидация и создание типизированной конфигурации
        return _create_typed_config(raw_config)
        
    except Exception as e:
        raise Exception(f"Ошибка загрузки конфигурации: {e}")

def _replace_env_vars(config: Dict[str, Any]) -> Dict[str, Any]:
    """Замена переменных окружения в конфигурации"""
    if isinstance(config, dict):
        return {k: _replace_env_vars(v) for k, v in config.items()}
    elif isinstance(config, str) and config.startswith("${") and config.endswith("}"):
        env_var = config[2:-1]
        return os.getenv(env_var, config)
    elif isinstance(config, list):
        return [_replace_env_vars(item) for item in config]
    else:
        return config

def _create_typed_config(raw_config: Dict[str, Any]) -> AppConfig:
    """Создание типизированной конфигурации"""
    
    # Telegram конфигурация
    telegram_config = TelegramConfig(
        token=raw_config['telegram']['token'],
        allowed_users=raw_config['telegram'].get('allowed_users', []),
        allowed_groups=raw_config['telegram'].get('allowed_groups', []),
        admin_users=raw_config['telegram'].get('admin_users', [])
    )
    
    # Prometheus конфигурация
    prometheus_config = PrometheusConfig(
        url=raw_config['prometheus']['url'],
        timeout=raw_config['prometheus'].get('timeout', 10)
    )
    
    # Docker конфигурация
    docker_config = DockerConfig(
        socket=raw_config['docker']['socket'],
        timeout=raw_config['docker'].get('timeout', 30)
    )
    
    # OpenAI конфигурация
    openai_config = OpenAIConfig(
        api_key=raw_config['openai']['api_key'],
        model=raw_config['openai']['model'],
        max_tokens=raw_config['openai'].get('max_tokens', 2000),
        temperature=raw_config['openai'].get('temperature', 0.7)
    )
    
    # AlertManager конфигурация
    alertmanager_config = AlertManagerConfig(
        url=raw_config['alertmanager']['url'],
        timeout=raw_config['alertmanager'].get('timeout', 10)
    )
    
    # Уведомления конфигурация
    notifications_config = NotificationConfig(
        enabled=raw_config['notifications'].get('enabled', True),
        check_interval=raw_config['notifications'].get('check_interval', 60),
        critical_only=raw_config['notifications'].get('critical_only', False)
    )
    
    # Сервисы конфигурация
    services_config = []
    for service_data in raw_config.get('services', []):
        service_config = ServiceConfig(
            name=service_data['name'],
            container=service_data['container'],
            health_url=service_data.get('health_url'),
            metrics_port=service_data.get('metrics_port')
        )
        services_config.append(service_config)
    
    return AppConfig(
        telegram=telegram_config,
        prometheus=prometheus_config,
        docker=docker_config,
        openai=openai_config,
        alertmanager=alertmanager_config,
        notifications=notifications_config,
        services=services_config
    )

def validate_config(config: AppConfig) -> bool:
    """Валидация конфигурации"""
    try:
        # Проверяем обязательные поля
        if not config.telegram.token:
            raise ValueError("Telegram token is required")
        
        if not config.openai.api_key:
            raise ValueError("OpenAI API key is required")
        
        if not config.prometheus.url:
            raise ValueError("Prometheus URL is required")
        
        if not config.docker.socket:
            raise ValueError("Docker socket is required")
        
        if not config.alertmanager.url:
            raise ValueError("AlertManager URL is required")
        
        # Проверяем сервисы
        if not config.services:
            raise ValueError("At least one service must be configured")
        
        return True
        
    except Exception as e:
        raise ValueError(f"Configuration validation failed: {e}")
