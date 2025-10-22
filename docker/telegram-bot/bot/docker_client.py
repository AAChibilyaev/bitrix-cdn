#!/usr/bin/env python3
"""
Клиент для работы с Docker API
"""

import logging
import docker
import asyncio
import aiohttp
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class DockerClient:
    """Клиент для работы с Docker API"""
    
    def __init__(self, config):
        self.config = config
        self.docker_socket = config.docker.socket
        self.client = docker.from_env()
        logger.info(f"Docker client initialized: {self.docker_socket}")
    
    async def get_containers_status(self) -> List[Dict[str, Any]]:
        """Получение статуса всех контейнеров"""
        try:
            containers = self.client.containers.list(all=True)
            containers_info = []
            
            for container in containers:
                # Получаем статус health check
                health_status = None
                try:
                    inspect = container.attrs
                    health = inspect.get('State', {}).get('Health', {})
                    if health:
                        health_status = health.get('Status', 'unknown')
                except Exception as e:
                    logger.warning(f"Ошибка получения health статуса для {container.name}: {e}")
                
                container_info = {
                    'name': container.name,
                    'status': container.status,
                    'health': health_status,
                    'image': container.image.tags[0] if container.image.tags else 'unknown',
                    'created': container.attrs['Created'],
                    'ports': list(container.ports.keys()) if container.ports else []
                }
                containers_info.append(container_info)
            
            return containers_info
        except Exception as e:
            logger.error(f"Ошибка получения статуса контейнеров: {e}")
            return []
    
    async def get_container_status(self, container_name: str) -> Dict[str, Any]:
        """Получение статуса конкретного контейнера"""
        try:
            container = self.client.containers.get(container_name)
            
            # Получаем статус health check
            health_status = None
            try:
                inspect = container.attrs
                health = inspect.get('State', {}).get('Health', {})
                if health:
                    health_status = health.get('Status', 'unknown')
            except Exception as e:
                logger.warning(f"Ошибка получения health статуса для {container_name}: {e}")
            
            return {
                'name': container.name,
                'status': container.status,
                'running': container.status == 'running',
                'health': health_status,
                'image': container.image.tags[0] if container.image.tags else 'unknown',
                'created': container.attrs['Created'],
                'ports': list(container.ports.keys()) if container.ports else []
            }
        except Exception as e:
            logger.error(f"Ошибка получения статуса контейнера {container_name}: {e}")
            return {'name': container_name, 'status': 'unknown', 'running': False}
    
    async def get_health_checks(self) -> Dict[str, Any]:
        """Выполнение health checks для всех сервисов"""
        health_checks = {}
        
        # Список сервисов для проверки
        services = [
            {'name': 'nginx', 'url': 'http://localhost/health'},
            {'name': 'webp-converter', 'url': 'http://localhost:8088/health'},
            {'name': 'prometheus', 'url': 'http://localhost:9090/api/v1/status'},
            {'name': 'grafana', 'url': 'http://localhost:3000/api/health'},
            {'name': 'alertmanager', 'url': 'http://localhost:9093/api/v2/status'},
            {'name': 'redis', 'url': 'http://localhost:6379'}  # Redis не имеет HTTP API
        ]
        
        for service in services:
            try:
                if service['name'] == 'redis':
                    # Специальная проверка для Redis
                    health_checks[service['name']] = await self._check_redis_health()
                else:
                    # HTTP проверки
                    health_checks[service['name']] = await self._check_http_health(service['url'])
            except Exception as e:
                logger.warning(f"Ошибка health check для {service['name']}: {e}")
                health_checks[service['name']] = {
                    'healthy': False,
                    'status': 'error',
                    'error': str(e)
                }
        
        return health_checks
    
    async def _check_http_health(self, url: str) -> Dict[str, Any]:
        """Проверка HTTP health endpoint"""
        try:
            async with aiohttp.ClientSession() as session:
                start_time = asyncio.get_event_loop().time()
                async with session.get(url, timeout=5) as response:
                    end_time = asyncio.get_event_loop().time()
                    response_time = int((end_time - start_time) * 1000)
                    
                    if response.status == 200:
                        return {
                            'healthy': True,
                            'status': 'ok',
                            'response_time': response_time,
                            'status_code': response.status
                        }
                    else:
                        return {
                            'healthy': False,
                            'status': f'http_{response.status}',
                            'response_time': response_time,
                            'status_code': response.status
                        }
        except asyncio.TimeoutError:
            return {
                'healthy': False,
                'status': 'timeout',
                'response_time': 5000
            }
        except Exception as e:
            return {
                'healthy': False,
                'status': 'error',
                'error': str(e)
            }
    
    async def _check_redis_health(self) -> Dict[str, Any]:
        """Проверка здоровья Redis"""
        try:
            # Получаем контейнер Redis
            redis_container = self.client.containers.get('cdn-redis')
            
            # Выполняем ping команду
            result = redis_container.exec_run('redis-cli -a bitrix_cdn_secure_2024 ping')
            
            if result.exit_code == 0 and b'PONG' in result.output:
                return {
                    'healthy': True,
                    'status': 'ok',
                    'response_time': 0
                }
            else:
                return {
                    'healthy': False,
                    'status': 'ping_failed',
                    'error': result.output.decode() if result.output else 'Unknown error'
                }
        except Exception as e:
            return {
                'healthy': False,
                'status': 'error',
                'error': str(e)
            }
    
    async def get_cache_statistics(self) -> Dict[str, Any]:
        """Получение статистики кеширования"""
        cache_stats = {}
        
        try:
            # Redis статистика
            redis_container = self.client.containers.get('cdn-redis')
            
            # Получаем информацию о памяти
            memory_result = redis_container.exec_run('redis-cli -a bitrix_cdn_secure_2024 info memory')
            if memory_result.exit_code == 0:
                memory_info = memory_result.output.decode()
                used_memory = None
                for line in memory_info.split('\n'):
                    if line.startswith('used_memory_human:'):
                        used_memory = line.split(':')[1].strip()
                        break
                
                # Получаем количество ключей
                keys_result = redis_container.exec_run('redis-cli -a bitrix_cdn_secure_2024 dbsize')
                keys_count = 'N/A'
                if keys_result.exit_code == 0:
                    keys_count = keys_result.output.decode().strip()
                
                # Получаем hit rate
                stats_result = redis_container.exec_run('redis-cli -a bitrix_cdn_secure_2024 info stats')
                hit_rate = 'N/A'
                if stats_result.exit_code == 0:
                    stats_info = stats_result.output.decode()
                    hits = 0
                    misses = 0
                    for line in stats_info.split('\n'):
                        if line.startswith('keyspace_hits:'):
                            hits = int(line.split(':')[1].strip())
                        elif line.startswith('keyspace_misses:'):
                            misses = int(line.split(':')[1].strip())
                    
                    if hits + misses > 0:
                        hit_rate = f"{(hits / (hits + misses) * 100):.1f}%"
                
                cache_stats['redis'] = {
                    'memory': used_memory,
                    'keys': keys_count,
                    'hit_rate': hit_rate
                }
        except Exception as e:
            logger.warning(f"Ошибка получения статистики Redis: {e}")
            cache_stats['redis'] = {'error': str(e)}
        
        try:
            # Nginx статистика (если доступна)
            nginx_container = self.client.containers.get('cdn-nginx')
            
            # Проверяем размер кеша
            cache_result = nginx_container.exec_run('du -sh /tmp/nginx_cache 2>/dev/null || echo "N/A"')
            cache_size = 'N/A'
            if cache_result.exit_code == 0:
                cache_size = cache_result.output.decode().strip()
            
            # Количество файлов в кеше
            files_result = nginx_container.exec_run('find /tmp/nginx_cache -type f | wc -l 2>/dev/null || echo "0"')
            files_count = '0'
            if files_result.exit_code == 0:
                files_count = files_result.output.decode().strip()
            
            cache_stats['nginx'] = {
                'cache_size': cache_size,
                'files': files_count
            }
        except Exception as e:
            logger.warning(f"Ошибка получения статистики Nginx: {e}")
            cache_stats['nginx'] = {'error': str(e)}
        
        return cache_stats
    
    async def restart_container(self, container_name: str) -> bool:
        """Перезапуск контейнера"""
        try:
            container = self.client.containers.get(container_name)
            container.restart()
            logger.info(f"Контейнер {container_name} перезапущен")
            return True
        except Exception as e:
            logger.error(f"Ошибка перезапуска контейнера {container_name}: {e}")
            return False
    
    async def get_container_logs(self, container_name: str, lines: int = 50) -> str:
        """Получение логов контейнера"""
        try:
            container = self.client.containers.get(container_name)
            logs = container.logs(tail=lines, timestamps=True).decode('utf-8')
            return logs
        except Exception as e:
            logger.error(f"Ошибка получения логов контейнера {container_name}: {e}")
            return f"Ошибка получения логов: {e}"
