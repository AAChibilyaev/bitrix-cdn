#!/usr/bin/env python3
"""
Кеширование для AI-анализа
"""

import asyncio
import json
import time
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from bot.types import AIAnalysisResult

@dataclass
class CacheEntry:
    """Запись в кеше"""
    data: AIAnalysisResult
    timestamp: float
    ttl: float

class AIAnalysisCache:
    """Кеш для AI-анализа"""
    
    def __init__(self, default_ttl: float = 300.0):  # 5 минут по умолчанию
        self.cache: Dict[str, CacheEntry] = {}
        self.default_ttl = default_ttl
        self._lock = asyncio.Lock()
    
    def _generate_key(self, system_data: str) -> str:
        """Генерация ключа кеша на основе данных системы"""
        import hashlib
        return hashlib.md5(system_data.encode()).hexdigest()
    
    async def get(self, system_data: str) -> Optional[AIAnalysisResult]:
        """Получение из кеша"""
        async with self._lock:
            key = self._generate_key(system_data)
            entry = self.cache.get(key)
            
            if entry is None:
                return None
            
            # Проверяем TTL
            if time.time() - entry.timestamp > entry.ttl:
                del self.cache[key]
                return None
            
            return entry.data
    
    async def set(self, system_data: str, result: AIAnalysisResult, ttl: Optional[float] = None) -> None:
        """Сохранение в кеш"""
        async with self._lock:
            key = self._generate_key(system_data)
            entry = CacheEntry(
                data=result,
                timestamp=time.time(),
                ttl=ttl or self.default_ttl
            )
            self.cache[key] = entry
    
    async def clear(self) -> None:
        """Очистка кеша"""
        async with self._lock:
            self.cache.clear()
    
    async def cleanup_expired(self) -> None:
        """Очистка истекших записей"""
        async with self._lock:
            current_time = time.time()
            expired_keys = [
                key for key, entry in self.cache.items()
                if current_time - entry.timestamp > entry.ttl
            ]
            for key in expired_keys:
                del self.cache[key]
    
    def get_stats(self) -> Dict[str, Any]:
        """Статистика кеша"""
        return {
            "entries_count": len(self.cache),
            "memory_usage": sum(
                len(json.dumps(asdict(entry.data), default=str))
                for entry in self.cache.values()
            )
        }

# Глобальный экземпляр кеша
analysis_cache = AIAnalysisCache()
