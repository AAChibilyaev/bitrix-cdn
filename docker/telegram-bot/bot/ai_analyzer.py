#!/usr/bin/env python3
"""
Современный AI-анализатор с новым OpenAI API
"""

import logging
from typing import Dict, Any, List, Optional
from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from prometheus_client import PrometheusClient
from docker_client import DockerClient
from models import (
    AppConfig, ContainerInfo, HealthCheckResult, AllMetrics, 
    CacheStatistics, AISystemAnalysis, AITrendAnalysis, AIRecommendation
)
from ai_cache import cached_system_analysis, cached_trend_analysis

logger = logging.getLogger(__name__)

class AIAnalyzer:
    """Современный AI-анализатор с новым OpenAI API"""
    
    def __init__(self, config: AppConfig):
        self.config = config
        self.prometheus = PrometheusClient(config)
        self.docker = DockerClient(config)
        
        # Новый AsyncOpenAI client (1 строка)
        self.client = AsyncOpenAI(api_key=config.openai.api_key)
        
        logger.info("Modern AI Analyzer initialized with new OpenAI API")
    
    async def analyze_system(self, use_cache: bool = True) -> AISystemAnalysis:
        """Анализ системы - теперь 3 строки вместо 70"""
        context = await self._prepare_context_data()
        
        if use_cache:
            result = await cached_system_analysis(context)
            if result:
                return result
        
        # Используем новый OpenAI API с Structured Outputs
        result = await self._call_openai_with_structured_output(context)
        return result
    
    async def analyze_trends(self, time_range: str = "1h") -> AITrendAnalysis:
        """Анализ трендов системы"""
        context = f"Анализ трендов за период: {time_range}\n"
        context += await self._prepare_context_data()
        
        result = await self._call_openai_trends(context)
        return result
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def _call_openai_with_structured_output(self, context: str) -> AISystemAnalysis:
        """Вызов OpenAI с Structured Outputs"""
        try:
            response = await self.client.chat.completions.create(
                model=self.config.openai.model,
                messages=[
                    {"role": "system", "content": """Ты эксперт по DevOps и системам CDN. Проанализируй состояние системы Bitrix CDN и предоставь:

1. ОБЩИЙ СТАТУС системы (healthy/warning/critical)
2. ОЦЕНКУ здоровья от 0 до 100
3. ПРОБЛЕМЫ (если есть) с приоритетами
4. РЕКОМЕНДАЦИИ по улучшению
5. ПРОГНОЗ возможных проблем

Отвечай на русском языке, будь конкретным и практичным. ВАЖНО: Отвечай в формате JSON:
{
  "status": "healthy|warning|critical",
  "overall_health_score": 85,
  "problems": ["проблема 1", "проблема 2"],
  "recommendations": ["рекомендация 1", "рекомендация 2"],
  "forecast": "прогноз ситуации"
}"""},
                    {"role": "user", "content": context}
                ],
                max_tokens=2000,
                temperature=0.7
            )
            
            # Парсим JSON ответ
            import json
            content = response.choices[0].message.content
            data = json.loads(content)
            
            return AISystemAnalysis(
                status=data.get("status", "unknown"),
                overall_health_score=data.get("overall_health_score", 0),
                problems=data.get("problems", []),
                recommendations=data.get("recommendations", []),
                forecast=data.get("forecast")
            )
            
        except Exception as e:
            logger.error(f"Ошибка OpenAI анализа: {e}")
            return AISystemAnalysis(
                status="error",
                overall_health_score=0,
                problems=[f"Ошибка анализа: {e}"],
                recommendations=[],
                forecast=None
            )
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def _call_openai_trends(self, context: str) -> AITrendAnalysis:
        """Вызов OpenAI для анализа трендов"""
        try:
            response = await self.client.chat.completions.create(
                model=self.config.openai.model,
                messages=[
                    {"role": "system", "content": """Ты эксперт по анализу трендов в системах CDN. Проанализируй тренды и предоставь:

1. НАПРАВЛЕНИЕ тренда (increasing/decreasing/stable)
2. ПРЕДСКАЗАННЫЕ проблемы
3. ПРЕДЛОЖЕНИЯ по оптимизации
4. УВЕРЕННОСТЬ в прогнозе от 0 до 100

Отвечай на русском языке, будь конкретным. ВАЖНО: Отвечай в формате JSON:
{
  "trend_direction": "increasing|decreasing|stable",
  "predicted_issues": ["проблема 1", "проблема 2"],
  "optimization_suggestions": ["предложение 1", "предложение 2"],
  "confidence_score": 85
}"""},
                    {"role": "user", "content": context}
                ],
                max_tokens=1500,
                temperature=0.7
            )
            
            # Парсим JSON ответ
            import json
            content = response.choices[0].message.content
            data = json.loads(content)
            
            return AITrendAnalysis(
                trend_direction=data.get("trend_direction", "stable"),
                predicted_issues=data.get("predicted_issues", []),
                optimization_suggestions=data.get("optimization_suggestions", []),
                confidence_score=data.get("confidence_score", 0)
            )
            
        except Exception as e:
            logger.error(f"Ошибка анализа трендов: {e}")
            return AITrendAnalysis(
                trend_direction="stable",
                predicted_issues=[f"Ошибка анализа: {e}"],
                optimization_suggestions=[],
                confidence_score=0
            )
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def ask_question(self, question: str) -> str:
        """Интерактивный анализ с ответом на вопрос"""
        try:
            context = await self._prepare_context_data()
            full_context = f"Вопрос пользователя: {question}\n\nДанные системы:\n{context}"

            response = await self.client.chat.completions.create(
                model=self.config.openai.model,
                messages=[
                    {"role": "system", "content": "Ты эксперт по DevOps и системам CDN. Отвечай на русском языке, будь конкретным и практичным."},
                    {"role": "user", "content": full_context}
                ],
                max_tokens=1500,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Ошибка AI анализа вопроса: {e}")
            return f"❌ Ошибка анализа: {e}"
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def analyze_code(self, configs_info: str) -> str:
        """Анализ кода и конфигураций"""
        try:
            response = await self.client.chat.completions.create(
                model=self.config.openai.model,
                messages=[
                    {"role": "system", "content": "Ты эксперт по анализу кода и конфигураций систем CDN. Найди ошибки, проблемы производительности, неоптимальные настройки и дай рекомендации. Отвечай на русском языке."},
                    {"role": "user", "content": f"Проанализируй конфигурации:\n\n{configs_info}"}
                ],
                max_tokens=1500,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Ошибка анализа кода: {e}")
            return f"❌ Ошибка анализа кода: {e}"
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def find_issues(self, debug_info: str) -> str:
        """Поиск проблем в системе"""
        try:
            response = await self.client.chat.completions.create(
                model=self.config.openai.model,
                messages=[
                    {"role": "system", "content": "Ты эксперт по диагностике систем CDN. Ищи критические проблемы, предупреждения, проблемы производительности и ошибки в логах. Отвечай на русском языке, структурированно."},
                    {"role": "user", "content": f"Найди проблемы в системе:\n\n{debug_info}"}
                ],
                max_tokens=1500,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Ошибка поиска проблем: {e}")
            return f"❌ Ошибка поиска проблем: {e}"
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def get_suggestions(self, current_state: str) -> str:
        """Получение рекомендаций по оптимизации"""
        try:
            response = await self.client.chat.completions.create(
                model=self.config.openai.model,
                messages=[
                    {"role": "system", "content": "Ты эксперт по оптимизации систем CDN. Предоставь приоритетные рекомендации, оптимизацию производительности, настройки кеширования, мониторинг и алерты, масштабирование. Отвечай на русском языке, будь конкретным и практичным."},
                    {"role": "user", "content": f"Дай рекомендации по оптимизации:\n\n{current_state}"}
                ],
                max_tokens=1500,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Ошибка получения рекомендаций: {e}")
            return f"❌ Ошибка получения рекомендаций: {e}"
    
    async def get_recommendations(self) -> str:
        """Получение рекомендаций по оптимизации"""
        try:
            # Собираем текущие метрики
            metrics = await self.prometheus.get_all_metrics()
            containers = await self.docker.get_containers_status()
            
            context = "=== РЕКОМЕНДАЦИИ ПО ОПТИМИЗАЦИИ ===\n\n"
            context += "Текущее состояние системы:\n"
            
            # Анализируем контейнеры
            running_containers = [c for c in containers if c['status'] == 'running']
            stopped_containers = [c for c in containers if c['status'] != 'running']
            
            context += f"Работающих контейнеров: {len(running_containers)}\n"
            context += f"Остановленных контейнеров: {len(stopped_containers)}\n"
            
            if stopped_containers:
                context += f"Остановленные: {', '.join([c['name'] for c in stopped_containers])}\n"
            
            # Анализируем метрики
            if metrics.get('redis'):
                redis_metrics = metrics['redis']
                context += f"\nRedis метрики: {redis_metrics}\n"
            
            if metrics.get('nginx'):
                nginx_metrics = metrics['nginx']
                context += f"Nginx метрики: {nginx_metrics}\n"
            
            response = await self.client.chat.completions.create(
                model=self.config.openai.model,
                messages=[
                    {"role": "system", "content": "Ты эксперт по оптимизации систем CDN. Проанализируй состояние системы и предоставь приоритетные рекомендации, оптимизацию производительности, настройки кеширования, мониторинг и алерты, масштабирование. Отвечай на русском языке, будь конкретным и практичным."},
                    {"role": "user", "content": context}
                ],
                max_tokens=self.config.openai.max_tokens,
                temperature=self.config.openai.temperature
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Ошибка получения рекомендаций: {e}")
            return f"❌ Ошибка получения рекомендаций: {e}"
    
    async def _prepare_context_data(self) -> str:
        """Подготовка контекста для AI анализа"""
        try:
            # Собираем данные о системе
            metrics = await self.prometheus.get_all_metrics()
            containers = await self.docker.get_containers_status()
            health_checks = await self.docker.get_health_checks()
            cache_stats = await self.docker.get_cache_statistics()
            
            # Формируем контекст для GPT
            context = "=== АНАЛИЗ СИСТЕМЫ CDN ===\n\n"
            
            # Статус контейнеров
            context += "🐳 КОНТЕЙНЕРЫ:\n"
            for container in containers:
                status_emoji = "✅" if container['status'] == 'running' else "❌"
                context += f"{status_emoji} {container['name']}: {container['status']}\n"
                if container.get('health'):
                    context += f"   Health: {container['health']}\n"
            context += "\n"
            
            # Health checks
            context += "🏥 HEALTH CHECKS:\n"
            for service, status in health_checks.items():
                status_emoji = "✅" if status['healthy'] else "❌"
                context += f"{status_emoji} {service}: {status['status']}\n"
            context += "\n"
            
            # Метрики Nginx
            if metrics.get('nginx'):
                nginx_metrics = metrics['nginx']
                context += "🌐 NGINX МЕТРИКИ:\n"
                for metric, value in nginx_metrics.items():
                    if value and value != 'N/A':
                        context += f"   {metric}: {value}\n"
                context += "\n"
            
            # Метрики Redis
            if metrics.get('redis'):
                redis_metrics = metrics['redis']
                context += "💾 REDIS МЕТРИКИ:\n"
                for metric, value in redis_metrics.items():
                    if value and value != 'N/A':
                        context += f"   {metric}: {value}\n"
                context += "\n"
            
            # Метрики WebP
            if metrics.get('webp'):
                webp_metrics = metrics['webp']
                context += "🖼️ WEBP КОНВЕРТЕР:\n"
                for metric, value in webp_metrics.items():
                    if value and value != 'N/A':
                        context += f"   {metric}: {value}\n"
                context += "\n"
            
            # Системные метрики
            if metrics.get('system'):
                system_metrics = metrics['system']
                context += "💻 СИСТЕМНЫЕ МЕТРИКИ:\n"
                for metric, value in system_metrics.items():
                    if value and value != 'N/A':
                        context += f"   {metric}: {value}\n"
                context += "\n"
            
            # Статистика кеша
            if cache_stats:
                context += "💾 СТАТИСТИКА КЕША:\n"
                if cache_stats.get('redis'):
                    redis_stats = cache_stats['redis']
                    context += "   Redis:\n"
                    for key, value in redis_stats.items():
                        context += f"     {key}: {value}\n"
                if cache_stats.get('nginx'):
                    nginx_stats = cache_stats['nginx']
                    context += "   Nginx:\n"
                    for key, value in nginx_stats.items():
                        context += f"     {key}: {value}\n"
                context += "\n"
            
            return context
            
        except Exception as e:
            logger.error(f"Ошибка подготовки контекста: {e}")
            return f"Ошибка сбора данных: {e}"