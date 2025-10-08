"""
WebP Converter Service - Main Entry Point
"""
import signal
import sys
import asyncio
from app.config import Config
from app.logger import setup_logger
from app.watcher import FileWatcher
from app.converter import ImageConverter
from app.queue_manager import QueueManager
from app.metrics import MetricsServer
from app.health import HealthCheckServer

class WebPConverterApp:
    def __init__(self):
        self.config = Config()
        self.logger = setup_logger(self.config.log_level)
        self.queue_manager = QueueManager(self.config)
        self.converter = ImageConverter(self.config, self.queue_manager)
        self.watcher = FileWatcher(self.config, self.queue_manager)
        self.metrics_server = MetricsServer(self.config, self.queue_manager)
        self.health_server = HealthCheckServer(self.config)
        self.running = True
        self.tasks = []

    async def start(self):
        """Start all application components"""
        self.logger.info("Starting WebP Converter service",
                        watch_dir=self.config.watch_dir,
                        quality=self.config.webp_quality)

        # Register signal handlers for graceful shutdown
        loop = asyncio.get_event_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(
                sig,
                lambda s=sig: asyncio.create_task(self.shutdown(s))
            )

        # Start components
        self.tasks = [
            asyncio.create_task(self.watcher.start()),
            asyncio.create_task(self.converter.start()),
            asyncio.create_task(self.metrics_server.start()),
            asyncio.create_task(self.health_server.start()),
        ]

        # Initial scan of existing files
        if self.config.initial_scan:
            await self.watcher.initial_scan()

        # Wait for all tasks
        try:
            await asyncio.gather(*self.tasks)
        except asyncio.CancelledError:
            self.logger.info("Tasks cancelled")

    async def shutdown(self, sig=None):
        """Graceful shutdown"""
        if sig:
            self.logger.info("Received shutdown signal", signal=sig.name)
        else:
            self.logger.info("Shutting down WebP Converter service")

        self.running = False

        # Stop components
        await self.converter.stop()
        await self.watcher.stop()
        await self.metrics_server.stop()
        await self.health_server.stop()

        # Cancel all tasks
        for task in self.tasks:
            task.cancel()

        self.logger.info("Shutdown complete")
        sys.exit(0)

def main():
    """Main entry point"""
    app = WebPConverterApp()
    try:
        asyncio.run(app.start())
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
