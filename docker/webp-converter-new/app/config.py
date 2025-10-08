"""
Configuration management from environment variables and config.yml
"""
import os
from dataclasses import dataclass, field
from typing import List
import yaml
from pathlib import Path

@dataclass
class Config:
    # Directories and files
    watch_dir: str = os.getenv('WEBP_WATCH_DIR', '/var/www/cdn/upload/resize_cache')
    extensions: List[str] = field(default_factory=list)

    # Conversion parameters
    webp_quality: int = int(os.getenv('WEBP_QUALITY', '85'))
    avif_quality: int = int(os.getenv('AVIF_QUALITY', '80'))
    min_file_size: int = int(os.getenv('WEBP_MIN_FILE_SIZE', '10240'))  # 10KB
    force_reconvert: bool = os.getenv('WEBP_FORCE_RECONVERT', 'false').lower() == 'true'
    
    # Format support
    enable_webp: bool = os.getenv('ENABLE_WEBP', 'true').lower() == 'true'
    enable_avif: bool = os.getenv('ENABLE_AVIF', 'true').lower() == 'true'

    # Performance
    worker_threads: int = int(os.getenv('WEBP_WORKER_THREADS', '4'))
    batch_size: int = int(os.getenv('WEBP_BATCH_SIZE', '10'))
    scan_interval: int = int(os.getenv('WEBP_SCAN_INTERVAL', '5'))
    max_queue_size: int = int(os.getenv('WEBP_MAX_QUEUE_SIZE', '1000'))
    rate_limit: int = int(os.getenv('WEBP_RATE_LIMIT', '100'))  # files/minute

    # Retry logic
    max_retries: int = 3
    retry_delay: int = 5

    # Servers
    metrics_port: int = int(os.getenv('METRICS_PORT', '9101'))
    health_port: int = int(os.getenv('HEALTH_PORT', '8088'))

    # Logging
    log_level: str = os.getenv('LOG_LEVEL', 'INFO')
    log_file: str = '/var/log/webp/converter.log'

    # Modes
    initial_scan: bool = True
    cleanup_orphaned: bool = False

    def __post_init__(self):
        """Load configuration from yaml and environment"""
        # Load from config.yml if exists
        config_path = Path('/app/config.yml')
        if config_path.exists():
            with open(config_path) as f:
                yaml_config = yaml.safe_load(f) or {}

            # Override with yaml values if not set by env
            for key, value in yaml_config.items():
                if not os.getenv(f'WEBP_{key.upper()}'):
                    if hasattr(self, key):
                        setattr(self, key, value)

        # Parse extensions
        if not self.extensions:
            ext_str = os.getenv('WEBP_EXTENSIONS', 'jpg,jpeg,png')
            self.extensions = [ext.strip() for ext in ext_str.split(',')]
