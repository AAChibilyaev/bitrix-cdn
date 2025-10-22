#!/usr/bin/env python3
"""
Система безопасности для Telegram бота
"""

import asyncio
import time
import hashlib
import hmac
import logging
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass
from enum import Enum
from bot.types import AppConfig, UserId, ChatId

logger = logging.getLogger(__name__)

class SecurityLevel(Enum):
    """Уровни безопасности"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class SecurityEvent:
    """Событие безопасности"""
    event_type: str
    user_id: UserId
    chat_id: ChatId
    timestamp: float
    severity: SecurityLevel
    description: str
    ip_address: Optional[str] = None

@dataclass
class RateLimit:
    """Ограничение скорости"""
    max_requests: int
    time_window: int  # секунды
    block_duration: int  # секунды

@dataclass
class UserSession:
    """Сессия пользователя"""
    user_id: UserId
    chat_id: ChatId
    is_admin: bool
    is_verified: bool
    last_activity: float
    request_count: int
    blocked_until: Optional[float] = None
    security_level: SecurityLevel = SecurityLevel.MEDIUM

class SecurityManager:
    """Менеджер безопасности"""
    
    def __init__(self, config: AppConfig):
        self.config = config
        self.user_sessions: Dict[UserId, UserSession] = {}
        self.security_events: List[SecurityEvent] = []
        self.blocked_users: Set[UserId] = set()
        self.rate_limits = {
            "default": RateLimit(max_requests=10, time_window=60, block_duration=300),
            "admin": RateLimit(max_requests=50, time_window=60, block_duration=600),
            "critical": RateLimit(max_requests=5, time_window=60, block_duration=1800)
        }
        self._setup_security_rules()
    
    def _setup_security_rules(self) -> None:
        """Настройка правил безопасности"""
        # Настройки по умолчанию
        self.max_events_history = 1000
        self.session_timeout = 3600  # 1 час
        self.failed_attempts_limit = 5
        self.suspicious_activity_threshold = 10
    
    async def authenticate_user(self, user_id: UserId, chat_id: ChatId, is_admin: bool = False) -> bool:
        """Аутентификация пользователя"""
        try:
            # Проверяем, заблокирован ли пользователь
            if user_id in self.blocked_users:
                await self._log_security_event(
                    "blocked_user_access",
                    user_id,
                    chat_id,
                    SecurityLevel.HIGH,
                    "Попытка доступа заблокированного пользователя"
                )
                return False
            
            # Проверяем разрешенных пользователей
            if not self._is_user_allowed(user_id, chat_id):
                await self._log_security_event(
                    "unauthorized_access",
                    user_id,
                    chat_id,
                    SecurityLevel.HIGH,
                    "Попытка неавторизованного доступа"
                )
                return False
            
            # Создаем или обновляем сессию
            await self._create_or_update_session(user_id, chat_id, is_admin)
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка аутентификации пользователя {user_id}: {e}")
            return False
    
    def _is_user_allowed(self, user_id: UserId, chat_id: ChatId) -> bool:
        """Проверка разрешенных пользователей"""
        # Проверяем пользователя
        if user_id in self.config.telegram.allowed_users:
            return True
        
        # Проверяем группу
        if chat_id in self.config.telegram.allowed_groups:
            return True
        
        # Если списки пустые, разрешаем всем (для тестирования)
        if not self.config.telegram.allowed_users and not self.config.telegram.allowed_groups:
            return True
        
        return False
    
    async def _create_or_update_session(self, user_id: UserId, chat_id: ChatId, is_admin: bool) -> None:
        """Создание или обновление сессии"""
        current_time = time.time()
        
        if user_id in self.user_sessions:
            session = self.user_sessions[user_id]
            session.last_activity = current_time
            session.request_count += 1
        else:
            session = UserSession(
                user_id=user_id,
                chat_id=chat_id,
                is_admin=is_admin,
                is_verified=True,
                last_activity=current_time,
                request_count=1
            )
        
        self.user_sessions[user_id] = session
    
    async def check_rate_limit(self, user_id: UserId) -> bool:
        """Проверка ограничения скорости"""
        if user_id not in self.user_sessions:
            return True
        
        session = self.user_sessions[user_id]
        current_time = time.time()
        
        # Проверяем блокировку
        if session.blocked_until and current_time < session.blocked_until:
            return False
        
        # Определяем лимит для пользователя
        rate_limit = self.rate_limits["default"]
        if session.is_admin:
            rate_limit = self.rate_limits["admin"]
        elif session.security_level == SecurityLevel.CRITICAL:
            rate_limit = self.rate_limits["critical"]
        
        # Проверяем количество запросов
        if session.request_count > rate_limit.max_requests:
            # Блокируем пользователя
            session.blocked_until = current_time + rate_limit.block_duration
            self.blocked_users.add(user_id)
            
            await self._log_security_event(
                "rate_limit_exceeded",
                user_id,
                session.chat_id,
                SecurityLevel.MEDIUM,
                f"Превышен лимит запросов: {session.request_count}/{rate_limit.max_requests}"
            )
            
            return False
        
        return True
    
    async def _log_security_event(
        self,
        event_type: str,
        user_id: UserId,
        chat_id: ChatId,
        severity: SecurityLevel,
        description: str,
        ip_address: Optional[str] = None
    ) -> None:
        """Логирование события безопасности"""
        event = SecurityEvent(
            event_type=event_type,
            user_id=user_id,
            chat_id=chat_id,
            timestamp=time.time(),
            severity=severity,
            description=description,
            ip_address=ip_address
        )
        
        self.security_events.append(event)
        
        # Ограничиваем размер истории
        if len(self.security_events) > self.max_events_history:
            self.security_events = self.security_events[-self.max_events_history:]
        
        # Логируем событие
        logger.warning(f"Security event: {event_type} - {description} (User: {user_id}, Severity: {severity})")
    
    async def detect_suspicious_activity(self, user_id: UserId) -> bool:
        """Обнаружение подозрительной активности"""
        if user_id not in self.user_sessions:
            return False
        
        session = self.user_sessions[user_id]
        current_time = time.time()
        
        # Анализируем события за последний час
        recent_events = [
            event for event in self.security_events
            if event.user_id == user_id and current_time - event.timestamp < 3600
        ]
        
        # Подсчитываем подозрительные события
        suspicious_events = [
            event for event in recent_events
            if event.severity in [SecurityLevel.HIGH, SecurityLevel.CRITICAL]
        ]
        
        if len(suspicious_events) >= self.suspicious_activity_threshold:
            await self._log_security_event(
                "suspicious_activity_detected",
                user_id,
                session.chat_id,
                SecurityLevel.HIGH,
                f"Обнаружена подозрительная активность: {len(suspicious_events)} событий за час"
            )
            
            # Повышаем уровень безопасности
            session.security_level = SecurityLevel.HIGH
            return True
        
        return False
    
    async def cleanup_expired_sessions(self) -> None:
        """Очистка истекших сессий"""
        current_time = time.time()
        expired_users = []
        
        for user_id, session in self.user_sessions.items():
            if current_time - session.last_activity > self.session_timeout:
                expired_users.append(user_id)
        
        for user_id in expired_users:
            del self.user_sessions[user_id]
            if user_id in self.blocked_users:
                self.blocked_users.remove(user_id)
    
    def get_security_stats(self) -> Dict[str, any]:
        """Статистика безопасности"""
        current_time = time.time()
        
        return {
            "active_sessions": len(self.user_sessions),
            "blocked_users": len(self.blocked_users),
            "total_events": len(self.security_events),
            "recent_events": len([
                event for event in self.security_events
                if current_time - event.timestamp < 3600
            ]),
            "high_severity_events": len([
                event for event in self.security_events
                if event.severity == SecurityLevel.HIGH
            ]),
            "critical_events": len([
                event for event in self.security_events
                if event.severity == SecurityLevel.CRITICAL
            ])
        }
    
    async def unblock_user(self, user_id: UserId) -> bool:
        """Разблокировка пользователя"""
        if user_id in self.blocked_users:
            self.blocked_users.remove(user_id)
            if user_id in self.user_sessions:
                self.user_sessions[user_id].blocked_until = None
            
            await self._log_security_event(
                "user_unblocked",
                user_id,
                self.user_sessions.get(user_id, UserSession(0, 0, False, False, 0, 0)).chat_id,
                SecurityLevel.LOW,
                "Пользователь разблокирован администратором"
            )
            return True
        
        return False
    
    def generate_security_report(self) -> str:
        """Генерация отчета по безопасности"""
        stats = self.get_security_stats()
        
        report = "🔒 *ОТЧЕТ ПО БЕЗОПАСНОСТИ*\n\n"
        report += f"👥 Активных сессий: {stats['active_sessions']}\n"
        report += f"🚫 Заблокированных пользователей: {stats['blocked_users']}\n"
        report += f"📊 Всего событий: {stats['total_events']}\n"
        report += f"⚠️ Событий за час: {stats['recent_events']}\n"
        report += f"🔴 Высокий приоритет: {stats['high_severity_events']}\n"
        report += f"🚨 Критические: {stats['critical_events']}\n"
        
        return report
