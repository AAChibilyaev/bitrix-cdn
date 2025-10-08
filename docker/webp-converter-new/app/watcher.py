"""
File system monitoring with watchdog
"""
import asyncio
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import structlog

logger = structlog.get_logger()

class ImageFileHandler(FileSystemEventHandler):
    def __init__(self, config, queue_manager, loop):
        self.config = config
        self.queue = queue_manager
        self.loop = loop

    def on_created(self, event):
        if not event.is_directory:
            self._handle_file(event.src_path)

    def on_modified(self, event):
        if not event.is_directory:
            self._handle_file(event.src_path)

    def _handle_file(self, file_path: str):
        """Handle detected file"""
        path = Path(file_path)

        # Check extension
        if path.suffix.lower().lstrip('.') in self.config.extensions:
            asyncio.run_coroutine_threadsafe(
                self.queue.put(str(path)),
                self.loop
            )
            logger.debug("File detected", file=str(path))

class FileWatcher:
    def __init__(self, config, queue_manager):
        self.config = config
        self.queue = queue_manager
        self.observer = Observer()
        self.event_handler = None

    async def start(self):
        """Start file monitoring"""
        logger.info("Starting file watcher",
                   directory=self.config.watch_dir)

        # Get current event loop and pass to handler
        loop = asyncio.get_running_loop()
        self.event_handler = ImageFileHandler(self.config, self.queue, loop)

        self.observer.schedule(
            self.event_handler,
            self.config.watch_dir,
            recursive=True
        )
        self.observer.start()

        # Keep observer alive
        while self.observer.is_alive():
            await asyncio.sleep(1)

    async def initial_scan(self):
        """Initial scan of existing files"""
        logger.info("Starting initial scan",
                   directory=self.config.watch_dir)

        watch_path = Path(self.config.watch_dir)
        file_count = 0

        for ext in self.config.extensions:
            for file_path in watch_path.rglob(f'*.{ext}'):
                await self.queue.put(str(file_path))
                file_count += 1

        logger.info("Initial scan complete", files_found=file_count)

    async def stop(self):
        """Stop monitoring"""
        logger.info("Stopping file watcher")
        self.observer.stop()
        self.observer.join()
