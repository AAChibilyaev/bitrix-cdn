#!/usr/bin/env python3
"""
Клиент для работы с Prometheus API
"""

import logging
from prometheus_api_client import PrometheusConnect
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class PrometheusClient:
    """Клиент для работы с Prometheus"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.prom_url = config['prometheus']['url']
        self.prom = PrometheusConnect(url=self.prom_url)
        logger.info(f"Prometheus client initialized: {self.prom_url}")
    
    async def get_nginx_metrics(self) -> Dict[str, Any]:
        """Получение метрик Nginx"""
        try:
            queries = {
                'requests_per_min': 'rate(nginx_http_requests_total[1m])',
                'active_connections': 'nginx_connections_active',
                'cache_hit_rate': 'rate(nginx_cache_hits_total[5m])',
                'upstream_response_time': 'nginx_upstream_response_time_seconds',
                'memory_usage': 'nginx_memory_usage_bytes'
            }
            
            metrics = {}
            for name, query in queries.items():
                try:
                    result = self.prom.custom_query(query)
                    if result:
                        metrics[name] = result[0].get('value', [None, 'N/A'])[1]
                except Exception as e:
                    logger.warning(f"Ошибка получения метрики {name}: {e}")
                    metrics[name] = 'N/A'
            
            return metrics
        except Exception as e:
            logger.error(f"Ошибка получения метрик Nginx: {e}")
            return {}
    
    async def get_redis_metrics(self) -> Dict[str, Any]:
        """Получение метрик Redis"""
        try:
            queries = {
                'memory_used': 'redis_memory_used_bytes',
                'keys_count': 'redis_db_keys',
                'hit_rate': 'rate(redis_keyspace_hits_total[5m])',
                'miss_rate': 'rate(redis_keyspace_misses_total[5m])',
                'connected_clients': 'redis_connected_clients',
                'ops_per_sec': 'redis_instantaneous_ops_per_sec'
            }
            
            metrics = {}
            for name, query in queries.items():
                try:
                    result = self.prom.custom_query(query)
                    if result:
                        value = result[0].get('value', [None, 'N/A'])[1]
                        if name in ['memory_used'] and value != 'N/A':
                            # Форматируем память в читаемый вид
                            try:
                                bytes_val = float(value)
                                if bytes_val < 1024:
                                    metrics[name] = f"{bytes_val:.0f} B"
                                elif bytes_val < 1024**2:
                                    metrics[name] = f"{bytes_val/1024:.1f} KB"
                                elif bytes_val < 1024**3:
                                    metrics[name] = f"{bytes_val/(1024**2):.1f} MB"
                                else:
                                    metrics[name] = f"{bytes_val/(1024**3):.1f} GB"
                            except:
                                metrics[name] = value
                        else:
                            metrics[name] = value
                except Exception as e:
                    logger.warning(f"Ошибка получения метрики {name}: {e}")
                    metrics[name] = 'N/A'
            
            return metrics
        except Exception as e:
            logger.error(f"Ошибка получения метрик Redis: {e}")
            return {}
    
    async def get_webp_metrics(self) -> Dict[str, Any]:
        """Получение метрик WebP конвертера"""
        try:
            queries = {
                'files_processed': 'webp_converter_files_processed_total',
                'files_failed': 'webp_converter_files_failed_total',
                'queue_size': 'webp_converter_queue_size',
                'processing_time': 'webp_converter_processing_time_seconds',
                'memory_usage': 'webp_converter_memory_usage_bytes'
            }
            
            metrics = {}
            for name, query in queries.items():
                try:
                    result = self.prom.custom_query(query)
                    if result:
                        value = result[0].get('value', [None, 'N/A'])[1]
                        if name in ['memory_usage'] and value != 'N/A':
                            # Форматируем память
                            try:
                                bytes_val = float(value)
                                if bytes_val < 1024:
                                    metrics[name] = f"{bytes_val:.0f} B"
                                elif bytes_val < 1024**2:
                                    metrics[name] = f"{bytes_val/1024:.1f} KB"
                                elif bytes_val < 1024**3:
                                    metrics[name] = f"{bytes_val/(1024**2):.1f} MB"
                                else:
                                    metrics[name] = f"{bytes_val/(1024**3):.1f} GB"
                            except:
                                metrics[name] = value
                        else:
                            metrics[name] = value
                except Exception as e:
                    logger.warning(f"Ошибка получения метрики {name}: {e}")
                    metrics[name] = 'N/A'
            
            return metrics
        except Exception as e:
            logger.error(f"Ошибка получения метрик WebP: {e}")
            return {}
    
    async def get_system_metrics(self) -> Dict[str, Any]:
        """Получение системных метрик"""
        try:
            queries = {
                'cpu_usage': 'rate(node_cpu_seconds_total[5m])',
                'memory_usage': 'node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes',
                'disk_usage': 'node_filesystem_size_bytes - node_filesystem_free_bytes',
                'load_average': 'node_load1',
                'network_tx': 'rate(node_network_transmit_bytes_total[5m])',
                'network_rx': 'rate(node_network_receive_bytes_total[5m])'
            }
            
            metrics = {}
            for name, query in queries.items():
                try:
                    result = self.prom.custom_query(query)
                    if result:
                        value = result[0].get('value', [None, 'N/A'])[1]
                        metrics[name] = value
                except Exception as e:
                    logger.warning(f"Ошибка получения метрики {name}: {e}")
                    metrics[name] = 'N/A'
            
            return metrics
        except Exception as e:
            logger.error(f"Ошибка получения системных метрик: {e}")
            return {}
    
    async def get_all_metrics(self) -> Dict[str, Any]:
        """Получение всех метрик"""
        try:
            all_metrics = {
                'nginx': await self.get_nginx_metrics(),
                'redis': await self.get_redis_metrics(),
                'webp': await self.get_webp_metrics(),
                'system': await self.get_system_metrics()
            }
            return all_metrics
        except Exception as e:
            logger.error(f"Ошибка получения всех метрик: {e}")
            return {}
    
    async def get_targets_status(self) -> Dict[str, Any]:
        """Получение статуса targets в Prometheus"""
        try:
            targets = self.prom.all_targets()
            targets_status = {}
            
            for target in targets:
                name = target.get('labels', {}).get('job', 'unknown')
                health = target.get('health', 'unknown')
                targets_status[name] = {
                    'health': health,
                    'last_scrape': target.get('lastScrape', 'unknown'),
                    'last_error': target.get('lastError', '')
                }
            
            return targets_status
        except Exception as e:
            logger.error(f"Ошибка получения статуса targets: {e}")
            return {}
