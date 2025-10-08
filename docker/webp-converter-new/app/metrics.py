"""
Prometheus metrics for monitoring
"""
import asyncio
import json
from aiohttp import web
from prometheus_client import Counter, Histogram, Gauge, Summary, generate_latest
import structlog

logger = structlog.get_logger()

class Metrics:
    def __init__(self):
        # Counters
        self.images_converted = Counter(
            'webp_images_converted_total',
            'Total number of images converted to WebP'
        )

        self.images_skipped = Counter(
            'webp_images_skipped_total',
            'Total number of images skipped (already exist)'
        )

        self.conversion_errors = Counter(
            'webp_conversion_errors_total',
            'Total number of conversion errors'
        )

        # Histogram for conversion duration
        self.conversion_duration = Histogram(
            'webp_conversion_duration_seconds',
            'Time spent converting images',
            buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0)
        )

        # Summary for file sizes
        self.original_size = Summary(
            'webp_original_size_bytes',
            'Size of original images in bytes'
        )

        self.webp_size = Summary(
            'webp_webp_size_bytes',
            'Size of WebP images in bytes'
        )

        # Gauge for current values
        self.queue_size = Gauge(
            'webp_queue_size',
            'Current size of the conversion queue'
        )

        self.compression_ratio = Gauge(
            'webp_compression_ratio',
            'Current compression ratio (percentage saved)'
        )

# Global metrics instance
metrics = Metrics()

class MetricsServer:
    def __init__(self, config, queue_manager=None):
        self.config = config
        self.queue_manager = queue_manager
        self.app = None
        self.runner = None
        self.site = None

    async def metrics_handler(self, request):
        """Serve Prometheus metrics"""
        metrics_output = generate_latest()
        # generate_latest() возвращает bytes, декодируем в str
        return web.Response(
            text=metrics_output.decode('utf-8'),
            content_type='text/plain; version=0.0.4; charset=utf-8'
        )

    async def queue_status_handler(self, request):
        """Serve queue status as JSON"""
        if self.queue_manager:
            status = self.queue_manager.get_status()
            return web.json_response(status)
        return web.json_response({'error': 'Queue manager not available'}, status=500)

    async def start(self):
        """Start HTTP server for metrics"""
        logger.info("Starting metrics server",
                   port=self.config.metrics_port)

        # Create aiohttp app
        self.app = web.Application()
        self.app.router.add_get('/metrics', self.metrics_handler)
        self.app.router.add_get('/queue/status', self.queue_status_handler)

        # Start server
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        self.site = web.TCPSite(self.runner, '0.0.0.0', self.config.metrics_port)
        await self.site.start()

        logger.info("Metrics server started",
                   port=self.config.metrics_port,
                   endpoints=['/metrics', '/queue/status'])

        # Keep running
        while True:
            await asyncio.sleep(3600)

    async def stop(self):
        """Stop metrics server"""
        logger.info("Stopping metrics server")
        if self.runner:
            await self.runner.cleanup()
