#!/usr/bin/env python3
"""
Вспомогательные функции для Telegram бота
"""

import os
import yaml
import logging
from typing import Dict, Any

def load_config() -> Dict[str, Any]:
    """Загрузка конфигурации из файла"""
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config.yml')
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # Замена переменных окружения
        config = _replace_env_vars(config)
        return config
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

def setup_logging(logging_config: Dict[str, Any]):
    """Настройка логирования"""
    level = logging_config.get('level', 'INFO')
    format_str = logging_config.get('format', 
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format=format_str
    )

def format_bytes(bytes_value: int) -> str:
    """Форматирование байтов в читаемый вид"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.1f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.1f} PB"

def format_duration(seconds: int) -> str:
    """Форматирование секунд в читаемый вид"""
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        return f"{seconds // 60}m {seconds % 60}s"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}h {minutes}m"

def escape_markdown(text: str) -> str:
    """Экранирование специальных символов для Markdown"""
    escape_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in escape_chars:
        text = text.replace(char, f'\\{char}')
    return text

def truncate_text(text: str, max_length: int = 4000) -> str:
    """Обрезка текста до максимальной длины"""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."

def is_authorized_user(user_id: int, config: Dict[str, Any]) -> bool:
    """Проверка авторизации пользователя"""
    allowed_users = config.get('telegram', {}).get('allowed_users', [])
    if not allowed_users:  # Пустой список = все пользователи
        return True
    return user_id in allowed_users
