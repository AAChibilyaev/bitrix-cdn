#!/usr/bin/env python3
"""
AI-анализатор для системы CDN с использованием GPT
"""

import logging
import openai
from typing import Dict, Any, List, Optional
from bot.prometheus_client import PrometheusClient
from bot.docker_client import DockerClient
from bot.types import (
    AppConfig, ContainerInfo, HealthCheckResult, AllMetrics, 
    CacheStatistics, AIAnalysisResult, Alert, NotificationIssue
)
from bot.ai_cache import analysis_cache

logger = logging.getLogger(__name__)

class AIAnalyzer:
    """AI-анализатор системы с использованием GPT"""
    
    def __init__(self, config: AppConfig):
        self.config = config
        self.prometheus = PrometheusClient(config)
        self.docker = DockerClient(config)
        
        # Настройка OpenAI
        openai.api_key = config.openai.api_key
        self.model = config.openai.model
        
        logger.info("AI Analyzer initialized")
    
    async def analyze_system(self, use_cache: bool = True) -> AIAnalysisResult:
        """Выполнение AI-анализа системы с кешированием"""
        try:
            # Собираем данные о системе
            metrics = await self.prometheus.get_all_metrics()
            containers = await self.docker.get_containers_status()
            health_checks = await self.docker.get_health_checks()
            cache_stats = await self.docker.get_cache_statistics()
            
            # Формируем контекст для GPT
            context = self._prepare_context(metrics, containers, health_checks, cache_stats)
            
            # Проверяем кеш
            if use_cache:
                cached_result = await analysis_cache.get(context)
                if cached_result:
                    logger.info("Using cached AI analysis result")
                    return cached_result
            
            # Выполняем анализ с GPT
            analysis_text = await self._perform_gpt_analysis(context)
            
            # Парсим результат в структурированный формат
            result = self._parse_analysis_result(analysis_text)
            
            # Сохраняем в кеш
            if use_cache:
                await analysis_cache.set(context, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Ошибка AI-анализа: {e}")
            return AIAnalysisResult(
                status="error",
                problems=[f"Ошибка выполнения AI-анализа: {e}"],
                recommendations=[],
                performance_score=None,
                forecast=None
            )
    
    def _prepare_context(self, metrics: Dict, containers: List, health_checks: Dict, cache_stats: Dict) -> str:
        """Подготовка контекста для GPT"""
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
    
    def _parse_analysis_result(self, analysis_text: str) -> AIAnalysisResult:
        """Парсинг результата AI-анализа в структурированный формат"""
        try:
            # Простой парсинг текста (можно улучшить с помощью regex)
            lines = analysis_text.split('\n')
            problems = []
            recommendations = []
            performance_score = None
            forecast = None
            
            current_section = None
            for line in lines:
                line = line.strip()
                if 'ПРОБЛЕМЫ' in line.upper() or 'ПРОБЛЕМ' in line.upper():
                    current_section = 'problems'
                elif 'РЕКОМЕНДАЦИИ' in line.upper() or 'РЕКОМЕНДАЦИ' in line.upper():
                    current_section = 'recommendations'
                elif 'ПРОГНОЗ' in line.upper():
                    current_section = 'forecast'
                elif line.startswith('•') or line.startswith('-') or line.startswith('*'):
                    if current_section == 'problems':
                        problems.append(line[1:].strip())
                    elif current_section == 'recommendations':
                        recommendations.append(line[1:].strip())
                elif current_section == 'forecast' and line:
                    forecast = line
            
            return AIAnalysisResult(
                status="completed",
                problems=problems,
                recommendations=recommendations,
                performance_score=performance_score,
                forecast=forecast
            )
        except Exception as e:
            logger.error(f"Ошибка парсинга результата AI-анализа: {e}")
            return AIAnalysisResult(
                status="error",
                problems=[f"Ошибка парсинга: {e}"],
                recommendations=[],
                performance_score=None,
                forecast=None
            )
    
    async def _perform_gpt_analysis(self, context: str) -> str:
        """Выполнение анализа с помощью GPT"""
        try:
            system_prompt = """Ты эксперт по DevOps и системам CDN. Проанализируй состояние системы Bitrix CDN и предоставь:

1. ОБЩИЙ СТАТУС системы (работает/есть проблемы)
2. ПРОБЛЕМЫ (если есть) с приоритетами
3. РЕКОМЕНДАЦИИ по улучшению
4. ПРОГНОЗ возможных проблем
5. ОЦЕНКА производительности

Отвечай на русском языке, будь конкретным и практичным. Используй эмодзи для лучшего восприятия."""

            response = await openai.ChatCompletion.acreate(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": context}
                ],
                max_tokens=2000,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Ошибка GPT анализа: {e}")
            return f"❌ Ошибка выполнения GPT анализа: {e}"
    
    async def analyze_trends(self, time_range: str = "1h") -> str:
        """Анализ трендов системы"""
        try:
            # Получаем исторические данные
            # TODO: Реализовать получение исторических данных из Prometheus
            
            context = f"Анализ трендов за период: {time_range}\n"
            context += "Данные будут получены из Prometheus..."
            
            system_prompt = """Ты эксперт по анализу трендов в системах CDN. Проанализируй тренды и предоставь:

1. ТРЕНДЫ производительности
2. ПАТТЕРНЫ использования
3. ПРЕДСКАЗАНИЯ нагрузки
4. РЕКОМЕНДАЦИИ по оптимизации

Отвечай на русском языке, будь конкретным."""

            response = await openai.ChatCompletion.acreate(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": context}
                ],
                max_tokens=1500,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Ошибка анализа трендов: {e}")
            return f"❌ Ошибка анализа трендов: {e}"
    
    async def ask_question(self, context: str) -> str:
        """Интерактивный анализ с ответом на вопрос"""
        try:
            system_prompt = """Ты эксперт по DevOps и системам CDN. Отвечай на вопросы пользователя, анализируя предоставленные данные системы.

Правила:
1. Отвечай на русском языке
2. Будь конкретным и практичным
3. Используй данные системы для обоснования ответов
4. Если видишь проблемы - предложи решения
5. Используй эмодзи для лучшего восприятия
6. Структурируй ответ с заголовками"""

            response = await openai.ChatCompletion.acreate(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": context}
                ],
                max_tokens=1500,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Ошибка AI анализа вопроса: {e}")
            return f"❌ Ошибка анализа: {e}"
    
    async def analyze_code(self, configs_info: str) -> str:
        """Анализ кода и конфигураций"""
        try:
            system_prompt = """Ты эксперт по анализу кода и конфигураций систем CDN. Проанализируй предоставленные логи и конфигурации.

Найди:
1. ОШИБКИ в конфигурациях
2. ПРОБЛЕМЫ производительности
3. НЕОПТИМАЛЬНЫЕ настройки
4. РЕКОМЕНДАЦИИ по улучшению

Отвечай на русском языке, будь конкретным."""

            response = await openai.ChatCompletion.acreate(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Проанализируй конфигурации:\n\n{configs_info}"}
                ],
                max_tokens=1500,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Ошибка анализа кода: {e}")
            return f"❌ Ошибка анализа кода: {e}"
    
    async def find_issues(self, debug_info: str) -> str:
        """Поиск проблем в системе"""
        try:
            system_prompt = """Ты эксперт по диагностике систем CDN. Проанализируй отладочную информацию и найди проблемы.

Ищи:
1. КРИТИЧЕСКИЕ проблемы (остановленные сервисы)
2. ПРЕДУПРЕЖДЕНИЯ (нездоровые сервисы)
3. ПРОБЛЕМЫ производительности
4. ОШИБКИ в логах

Отвечай на русском языке, структурированно."""

            response = await openai.ChatCompletion.acreate(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Найди проблемы в системе:\n\n{debug_info}"}
                ],
                max_tokens=1500,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Ошибка поиска проблем: {e}")
            return f"❌ Ошибка поиска проблем: {e}"
    
    async def get_suggestions(self, current_state: str) -> str:
        """Получение рекомендаций по оптимизации"""
        try:
            system_prompt = """Ты эксперт по оптимизации систем CDN. Проанализируй текущее состояние и дай рекомендации.

Предоставь:
1. ПРИОРИТЕТНЫЕ рекомендации
2. ОПТИМИЗАЦИЯ производительности
3. НАСТРОЙКИ кеширования
4. МОНИТОРИНГ и алерты
5. МАСШТАБИРОВАНИЕ

Отвечай на русском языке, будь конкретным и практичным."""

            response = await openai.ChatCompletion.acreate(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
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
            
            system_prompt = """Ты эксперт по оптимизации систем CDN. Проанализируй состояние системы и предоставь:

1. ПРИОРИТЕТНЫЕ РЕКОМЕНДАЦИИ
2. ОПТИМИЗАЦИЯ ПРОИЗВОДИТЕЛЬНОСТИ
3. НАСТРОЙКИ КЕШИРОВАНИЯ
4. МОНИТОРИНГ И АЛЕРТЫ
5. МАСШТАБИРОВАНИЕ

Отвечай на русском языке, будь конкретным и практичным."""

            response = await openai.ChatCompletion.acreate(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": context}
                ],
                max_tokens=2000,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Ошибка получения рекомендаций: {e}")
            return f"❌ Ошибка получения рекомендаций: {e}"
