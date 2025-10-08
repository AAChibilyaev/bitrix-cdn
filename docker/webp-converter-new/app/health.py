"""
HTTP Health check endpoints
"""
import asyncio
import os
from aiohttp import web
import structlog

logger = structlog.get_logger()

class HealthCheckServer:
    def __init__(self, config):
        self.config = config
        self.app = web.Application()
        self.app.router.add_get('/health', self.health_check)
        self.app.router.add_get('/ready', self.readiness_check)
        self.runner = None

    async def health_check(self, request):
        """Liveness probe - service is running"""
        return web.json_response({
            'status': 'healthy',
            'service': 'webp-converter'
        })

    async def readiness_check(self, request):
        """Readiness probe - service is ready to accept requests"""
        # Check watch directory availability
        if not os.path.exists(self.config.watch_dir):
            return web.json_response({
                'status': 'not ready',
                'reason': 'watch directory not available'
            }, status=503)

        return web.json_response({
            'status': 'ready',
            'watch_dir': self.config.watch_dir
        })

    async def start(self):
        """Start HTTP server"""
        logger.info("Starting health check server",
                   port=self.config.health_port)

        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        site = web.TCPSite(
            self.runner,
            '0.0.0.0',
            self.config.health_port
        )
        await site.start()

        # Keep running
        while True:
            await asyncio.sleep(3600)

    async def stop(self):
        """Stop server"""
        if self.runner:
            logger.info("Stopping health check server")
            await self.runner.cleanup()
