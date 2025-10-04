#!/usr/bin/env python3
"""
WebP Converter HTTP Service
HTTP API для конвертации изображений в WebP + File watcher

Author: Chibilyaev Alexandr <info@aachibilyaev.com>
Company: AAChibilyaev LTD
"""

import os
import sys
import time
import hashlib
import subprocess
import logging
import threading
from pathlib import Path
from typing import Optional, Tuple
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import json
import redis
from PIL import Image
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Configuration
QUALITY = int(os.environ.get('WEBP_QUALITY', 85))
MAX_WIDTH = int(os.environ.get('MAX_WIDTH', 2048))
MAX_HEIGHT = int(os.environ.get('MAX_HEIGHT', 2048))
CACHE_DIR = Path(os.environ.get('CACHE_DIR', '/var/cache/webp'))
SOURCE_DIR = Path(os.environ.get('SOURCE_DIR', '/mnt/bitrix'))
REDIS_HOST = os.environ.get('REDIS_HOST', 'redis')
REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/converter/converter.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('webp-converter')

# Redis connection
try:
    redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
    redis_client.ping()
    logger.info("Connected to Redis")
except:
    redis_client = None
    logger.warning("Redis not available, running without cache metadata")


class WebPConverter:
    """WebP conversion handler"""
    
    def __init__(self):
        self.supported_formats = {'.jpg', '.jpeg', '.png', '.gif', '.bmp'}
        self.stats = {
            'converted': 0,
            'skipped': 0,
            'failed': 0,
            'total_saved': 0
        }
    
    def get_cache_path(self, source_path: Path) -> Path:
        """Get cache path for source file"""
        relative_path = source_path.relative_to(SOURCE_DIR)
        cache_path = CACHE_DIR / relative_path
        return cache_path.with_suffix(cache_path.suffix + '.webp')
    
    def needs_conversion(self, source_path: Path, cache_path: Path) -> bool:
        """Check if conversion is needed"""
        if not cache_path.exists():
            return True
        
        # Check if source is newer
        source_mtime = source_path.stat().st_mtime
        cache_mtime = cache_path.stat().st_mtime
        
        return source_mtime > cache_mtime
    
    def convert_image(self, source_path: Path) -> Optional[Path]:
        """Convert image to WebP format"""
        if source_path.suffix.lower() not in self.supported_formats:
            return None
        
        cache_path = self.get_cache_path(source_path)
        
        # Check if conversion needed
        if not self.needs_conversion(source_path, cache_path):
            logger.debug(f"Skipping {source_path} - already converted")
            self.stats['skipped'] += 1
            return cache_path
        
        # Create cache directory
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            # Get original size
            original_size = source_path.stat().st_size
            
            # Convert using cwebp for better quality
            cmd = [
                'cwebp',
                '-q', str(QUALITY),
                '-mt',  # Multi-threading
                '-af',  # Auto-filter
                '-m', '6',  # Compression method
                '-resize', str(MAX_WIDTH), str(MAX_HEIGHT),
                str(source_path),
                '-o', str(cache_path)
            ]
            
            # Add alpha quality for PNG
            if source_path.suffix.lower() == '.png':
                cmd.extend(['-alpha_q', '100'])
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                # Get new size
                webp_size = cache_path.stat().st_size
                saved = original_size - webp_size
                # Правильный расчёт: положительное значение = экономия, отрицательное = увеличение
                if original_size > 0:
                    saved_percent = (saved / original_size) * 100
                else:
                    saved_percent = 0
                
                self.stats['converted'] += 1
                self.stats['total_saved'] += saved
                
                # Логируем результат конвертации
                if saved > 0:
                    logger.info(f"Converted {source_path.name}: "
                              f"{original_size:,} -> {webp_size:,} bytes "
                              f"(saved {saved_percent:.1f}%)")
                else:
                    logger.warning(f"Converted {source_path.name}: "
                                 f"{original_size:,} -> {webp_size:,} bytes "
                                 f"(increased by {abs(saved_percent):.1f}%)")
                
                # Store metadata in Redis if available
                if redis_client:
                    key = f"webp:{source_path}"
                    redis_client.hset(key, mapping={
                        'original_size': original_size,
                        'webp_size': webp_size,
                        'saved': saved,
                        'quality': QUALITY,
                        'timestamp': time.time()
                    })
                    redis_client.expire(key, 86400 * 30)  # 30 days
                
                return cache_path
            else:
                logger.error(f"Failed to convert {source_path}: {result.stderr}")
                self.stats['failed'] += 1
                return None
                
        except Exception as e:
            logger.error(f"Error converting {source_path}: {e}")
            self.stats['failed'] += 1
            return None
    
    def convert_directory(self, directory: Path):
        """Convert all images in directory"""
        logger.info(f"Converting directory: {directory}")
        
        for ext in self.supported_formats:
            for image_path in directory.rglob(f"*{ext}"):
                self.convert_image(image_path)
                
                # Small delay to prevent overload
                if self.stats['converted'] % 10 == 0:
                    time.sleep(0.1)
    
    def cleanup_orphaned(self):
        """Remove WebP files for deleted originals"""
        logger.info("Cleaning orphaned WebP files...")
        removed = 0
        
        for webp_path in CACHE_DIR.rglob("*.webp"):
            # Reconstruct original path
            relative_path = webp_path.relative_to(CACHE_DIR)
            original_path = SOURCE_DIR / str(relative_path).replace('.webp', '')
            
            if not original_path.exists():
                logger.info(f"Removing orphaned: {webp_path}")
                webp_path.unlink()
                removed += 1
                
                # Remove from Redis
                if redis_client:
                    redis_client.delete(f"webp:{original_path}")
        
        logger.info(f"Removed {removed} orphaned files")
    
    def show_stats(self):
        """Display conversion statistics"""
        logger.info("=== Conversion Statistics ===")
        logger.info(f"Converted: {self.stats['converted']}")
        logger.info(f"Skipped: {self.stats['skipped']}")
        logger.info(f"Failed: {self.stats['failed']}")
        
        if self.stats['total_saved'] > 0:
            saved_mb = self.stats['total_saved'] / (1024 * 1024)
            logger.info(f"Total saved: {saved_mb:.2f} MB")


class ImageEventHandler(FileSystemEventHandler):
    """Handle file system events for image files"""
    
    def __init__(self, converter: WebPConverter):
        self.converter = converter
    
    def on_created(self, event):
        if not event.is_directory:
            path = Path(event.src_path)
            if path.suffix.lower() in self.converter.supported_formats:
                logger.info(f"New image detected: {path}")
                self.converter.convert_image(path)
    
    def on_modified(self, event):
        if not event.is_directory:
            path = Path(event.src_path)
            if path.suffix.lower() in self.converter.supported_formats:
                logger.info(f"Image modified: {path}")
                self.converter.convert_image(path)
    
    def on_deleted(self, event):
        if not event.is_directory:
            path = Path(event.src_path)
            if path.suffix.lower() in self.converter.supported_formats:
                # Remove corresponding WebP
                cache_path = self.converter.get_cache_path(path)
                if cache_path.exists():
                    logger.info(f"Removing WebP for deleted image: {path}")
                    cache_path.unlink()
                    
                    # Remove from Redis
                    if redis_client:
                        redis_client.delete(f"webp:{path}")


class ConversionRequestHandler(BaseHTTPRequestHandler):
    """HTTP handler для запросов конвертации"""
    
    def __init__(self, *args, converter=None, **kwargs):
        self.converter = converter
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Handle GET request для конвертации"""
        try:
            # Парсим URL
            parsed = urllib.parse.urlparse(self.path)
            
            if parsed.path == '/health':
                self.send_health_response()
                return
            elif parsed.path == '/metrics':
                self.send_metrics_response()
                return
            elif parsed.path.startswith('/convert-resize'):
                # Обработка resize_cache изображений
                image_path = parsed.path.replace('/convert-resize', '')
                self.handle_resize_conversion(image_path)
                return
            elif parsed.path.startswith('/convert'):
                # Получаем путь к файлу из URL
                image_path = parsed.path.replace('/convert', '')
                self.handle_conversion(image_path)
                return
            else:
                self.send_error(404, "Not Found")
                
        except Exception as e:
            logger.error(f"Request error: {e}")
            self.send_error(500, str(e))
    
    def handle_conversion(self, image_path: str):
        """Handle image conversion request"""
        try:
            # Проверяем Accept header для WebP
            accept_header = self.headers.get('Accept', '')
            if 'image/webp' not in accept_header:
                # Браузер не поддерживает WebP, отдаём оригинал
                self.serve_original(image_path)
                return
            
            source_path = SOURCE_DIR / image_path.lstrip('/')
            
            if not source_path.exists():
                self.send_error(404, "Image not found")
                return
            
            # Конвертируем в WebP
            webp_path = self.converter.convert_image(source_path)
            
            if webp_path and webp_path.exists():
                self.serve_webp_file(webp_path)
            else:
                # Если конвертация не удалась, отдаём оригинал
                self.serve_original_file(source_path)
                
        except Exception as e:
            logger.error(f"Conversion error: {e}")
            self.send_error(500, "Conversion failed")
    
    def serve_webp_file(self, file_path: Path):
        """Serve WebP file"""
        self.send_response(200)
        self.send_header('Content-Type', 'image/webp')
        self.send_header('Content-Length', str(file_path.stat().st_size))
        self.send_header('Cache-Control', 'public, max-age=31536000')
        self.end_headers()
        
        with open(file_path, 'rb') as f:
            self.wfile.write(f.read())
    
    def serve_original_file(self, file_path: Path):
        """Serve original file"""
        content_type = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg', 
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.bmp': 'image/bmp'
        }.get(file_path.suffix.lower(), 'application/octet-stream')
        
        self.send_response(200)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(file_path.stat().st_size))
        self.send_header('Cache-Control', 'public, max-age=31536000')
        self.end_headers()
        
        with open(file_path, 'rb') as f:
            self.wfile.write(f.read())
    
    def serve_original(self, image_path: str):
        """Redirect to original file"""
        self.send_response(302)
        self.send_header('Location', f'/mnt/bitrix{image_path}')
        self.end_headers()
    
    def handle_resize_conversion(self, image_path: str):
        """Handle resize_cache image conversion"""
        try:
            # resize_cache хранится локально
            source_path = Path('/var/www/cdn') / image_path.lstrip('/')

            if not source_path.exists():
                logger.error(f"Resize cache image not found: {source_path}")
                self.send_error(404, "Resize cache image not found")
                return

            # Проверяем Accept header для WebP
            accept_header = self.headers.get('Accept', '')
            if 'image/webp' not in accept_header:
                # Браузер не поддерживает WebP
                self.serve_original_file(source_path)
                return

            # Путь для WebP версии (хранится рядом с оригиналом)
            webp_path = source_path.with_suffix(source_path.suffix + '.webp')

            # Конвертируем если нужно
            if not webp_path.exists() or source_path.stat().st_mtime > webp_path.stat().st_mtime:
                # Конвертируем в WebP напрямую (не через convert_image, т.к. resize_cache не в SOURCE_DIR)
                try:
                    cmd = [
                        'cwebp',
                        '-q', str(QUALITY),
                        str(source_path),
                        '-o', str(webp_path)
                    ]
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

                    if result.returncode == 0:
                        logger.info(f"Converted resize_cache: {source_path} -> {webp_path}")
                        self.converter.stats['converted'] += 1

                        # Update Redis stats
                        if redis_client:
                            redis_client.set(f"webp:resize:{source_path}", str(webp_path))
                    else:
                        logger.error(f"Conversion failed: {result.stderr}")
                        self.converter.stats['failed'] += 1
                        webp_path = None
                except subprocess.TimeoutExpired:
                    logger.error(f"Conversion timeout: {source_path}")
                    self.converter.stats['failed'] += 1
                    webp_path = None
                except Exception as conv_error:
                    logger.error(f"Conversion exception: {conv_error}")
                    self.converter.stats['failed'] += 1
                    webp_path = None

            if webp_path and webp_path.exists():
                self.serve_webp_file(webp_path)
            else:
                self.serve_original_file(source_path)

        except Exception as e:
            logger.error(f"Resize conversion error: {e}")
            self.send_error(500, "Conversion failed")
    
    def send_health_response(self):
        """Health check response"""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        
        health = {
            'status': 'healthy',
            'uptime': int(time.time()),
            'stats': self.converter.stats if self.converter else {}
        }
        self.wfile.write(json.dumps(health).encode())
    
    def send_metrics_response(self):
        """Prometheus metrics"""
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        
        if self.converter:
            metrics = f"""# HELP webp_conversions_total Total WebP conversions
# TYPE webp_conversions_total counter
webp_conversions_total{{result="success"}} {self.converter.stats['converted']}
webp_conversions_total{{result="failed"}} {self.converter.stats['failed']}
webp_conversions_total{{result="skipped"}} {self.converter.stats['skipped']}

# HELP webp_bytes_saved_total Total bytes saved by WebP
# TYPE webp_bytes_saved_total counter
webp_bytes_saved_total {self.converter.stats['total_saved']}
"""
        else:
            metrics = "# No converter available\n"
        
        self.wfile.write(metrics.encode())
    
    def log_message(self, format, *args):
        """Suppress default HTTP logging"""
        pass


def start_http_server(converter: WebPConverter):
    """Start HTTP server for conversion API"""
    handler = lambda *args, **kwargs: ConversionRequestHandler(*args, converter=converter, **kwargs)
    
    server = HTTPServer(('0.0.0.0', 8080), handler)
    logger.info("HTTP server started on port 8080")
    server.serve_forever()


def start_file_watcher(converter: WebPConverter):
    """Start file system watcher"""
    event_handler = ImageEventHandler(converter)
    observer = Observer()
    
    if SOURCE_DIR.exists():
        observer.schedule(event_handler, str(SOURCE_DIR), recursive=True)
        observer.start()
        logger.info("File system observer started")
        
        try:
            while True:
                time.sleep(300)  # 5 minutes
                
                # Periodic cleanup
                if converter.stats['converted'] % 100 == 0:
                    converter.cleanup_orphaned()
                    
        except KeyboardInterrupt:
            observer.stop()
            logger.info("File watcher shutting down...")
        
        observer.join()
    else:
        logger.warning(f"Source directory not found: {SOURCE_DIR}")


def main():
    """Main service entry point"""
    logger.info("Starting WebP Converter HTTP Service")
    logger.info(f"Source: {SOURCE_DIR}")
    logger.info(f"Cache: {CACHE_DIR}")
    logger.info(f"Quality: {QUALITY}")
    
    # Create converter
    converter = WebPConverter()
    
    # Убеждаемся что директории существуют
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    
    # Запускаем file watcher в отдельном потоке
    watcher_thread = threading.Thread(target=start_file_watcher, args=(converter,))
    watcher_thread.daemon = True
    watcher_thread.start()
    
    # Запускаем HTTP сервер в основном потоке
    try:
        start_http_server(converter)
    except KeyboardInterrupt:
        logger.info("Shutting down HTTP service...")
        converter.show_stats()


if __name__ == '__main__':
    main()
