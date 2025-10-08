"""
Async image conversion to WebP and AVIF formats
"""
import os
import asyncio
from pathlib import Path
from PIL import Image
from app.metrics import metrics
import structlog

# AVIF support via pillow-heif
try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
    AVIF_SUPPORT = True
except ImportError:
    AVIF_SUPPORT = False

logger = structlog.get_logger()

class ImageConverter:
    def __init__(self, config, queue_manager):
        self.config = config
        self.queue = queue_manager
        self.running = True
        self.workers = []

    async def start(self):
        """Start worker threads for queue processing"""
        logger.info("Starting image converter workers",
                   workers=self.config.worker_threads)

        for i in range(self.config.worker_threads):
            worker = asyncio.create_task(self._worker(i))
            self.workers.append(worker)

        await asyncio.gather(*self.workers, return_exceptions=True)

    async def _worker(self, worker_id):
        """Worker to process files from queue"""
        logger.info("Worker started", worker_id=worker_id)

        while self.running:
            try:
                file_path = await self.queue.get()
                if file_path is None:
                    break

                await self._process_file(file_path, worker_id)
                self.queue.task_done()

            except Exception as e:
                logger.error("Worker error", worker_id=worker_id, error=str(e))
                await asyncio.sleep(self.config.retry_delay)

    async def _process_file(self, file_path, worker_id):
        """Process single file"""
        start_time = asyncio.get_event_loop().time()
        try:
            file_path = Path(file_path)
            webp_path = file_path.with_suffix(file_path.suffix + '.webp')
            avif_path = file_path.with_suffix(file_path.suffix + '.avif')

            # Mark as processing
            self.queue.mark_processing(worker_id, str(file_path.name))

            # Check if WebP conversion needed
            webp_needed = self.config.enable_webp and self._should_convert(file_path, webp_path)
            # Check if AVIF conversion needed
            avif_needed = self.config.enable_avif and self._should_convert(file_path, avif_path)

            if not webp_needed and not avif_needed:
                metrics.images_skipped.inc()
                logger.debug("Skipping file", file=str(file_path),
                           reason="both formats exist and newer or disabled")
                duration = asyncio.get_event_loop().time() - start_time
                self.queue.mark_completed(worker_id, str(file_path.name), 'skipped', duration)
                return

            # Convert WebP with retry logic
            if webp_needed:
                for attempt in range(self.config.max_retries):
                    try:
                        await self._convert_to_webp(file_path, webp_path, worker_id)
                        break
                    except Exception as e:
                        if attempt == self.config.max_retries - 1:
                            raise
                        logger.warning("Retry WebP conversion",
                                     file=str(file_path),
                                     attempt=attempt + 1,
                                     error=str(e))
                        await asyncio.sleep(self.config.retry_delay)

            # Convert AVIF with retry logic
            if avif_needed:
                for attempt in range(self.config.max_retries):
                    try:
                        await self._convert_to_avif(file_path, avif_path, worker_id)
                        break
                    except Exception as e:
                        if attempt == self.config.max_retries - 1:
                            raise
                        logger.warning("Retry AVIF conversion",
                                     file=str(file_path),
                                     attempt=attempt + 1,
                                     error=str(e))
                        await asyncio.sleep(self.config.retry_delay)

            duration = asyncio.get_event_loop().time() - start_time
            self.queue.mark_completed(worker_id, str(file_path.name), 'success', duration)

        except Exception as e:
            metrics.conversion_errors.inc()
            duration = asyncio.get_event_loop().time() - start_time
            self.queue.mark_completed(worker_id, str(file_path.name), 'error', duration, str(e))
            logger.error("Conversion failed",
                        file=str(file_path),
                        error=str(e))

    def _should_convert(self, original_path: Path, webp_path: Path) -> bool:
        """Check if conversion is needed"""
        if self.config.force_reconvert:
            return True

        if not original_path.exists():
            return False

        # Check minimum file size
        if original_path.stat().st_size < self.config.min_file_size:
            return False

        # Check if webp exists and is newer
        if webp_path.exists():
            if webp_path.stat().st_mtime >= original_path.stat().st_mtime:
                return False

        return True

    async def _convert_to_webp(self, original_path: Path, webp_path: Path, worker_id: int):
        """Convert image to WebP"""
        start_time = asyncio.get_event_loop().time()

        # Convert in thread pool
        await asyncio.to_thread(self._convert_sync, original_path, webp_path)

        # Set permissions
        os.chown(webp_path, 33, 33)  # www-data
        os.chmod(webp_path, 0o644)

        # Metrics
        duration = asyncio.get_event_loop().time() - start_time
        original_size = original_path.stat().st_size
        webp_size = webp_path.stat().st_size
        compression_ratio = (1 - webp_size / original_size) * 100

        metrics.images_converted.inc()
        metrics.conversion_duration.observe(duration)
        metrics.original_size.observe(original_size)
        metrics.webp_size.observe(webp_size)
        metrics.compression_ratio.set(compression_ratio)

        logger.info("Image converted",
                   worker_id=worker_id,
                   file=str(original_path.name),
                   original_size=original_size,
                   webp_size=webp_size,
                   compression=f"{compression_ratio:.1f}%",
                   duration=f"{duration:.2f}s")

    async def _convert_to_avif(self, original_path: Path, avif_path: Path, worker_id: int):
        """Convert image to AVIF"""
        start_time = asyncio.get_event_loop().time()

        # Convert in thread pool
        await asyncio.to_thread(self._convert_avif_sync, original_path, avif_path)

        # Set permissions
        os.chown(avif_path, 33, 33)  # www-data
        os.chmod(avif_path, 0o644)

        # Metrics
        duration = asyncio.get_event_loop().time() - start_time
        original_size = original_path.stat().st_size
        avif_size = avif_path.stat().st_size
        compression_ratio = (1 - avif_size / original_size) * 100

        metrics.avif_images_converted.inc()
        metrics.avif_conversion_duration.observe(duration)
        metrics.original_size.observe(original_size)
        metrics.avif_size.observe(avif_size)
        metrics.avif_compression_ratio.set(compression_ratio)

        logger.info("Image converted to AVIF",
                   worker_id=worker_id,
                   file=str(original_path.name),
                   original_size=original_size,
                   avif_size=avif_size,
                   compression=f"{compression_ratio:.1f}%",
                   duration=f"{duration:.2f}s")

    def _convert_sync(self, original_path: Path, webp_path: Path):
        """Synchronous WebP conversion (runs in thread pool)"""
        with Image.open(original_path) as img:
            # Convert to RGB if necessary
            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGBA')
            elif img.mode != 'RGB':
                img = img.convert('RGB')

            # Save as WebP
            img.save(webp_path,
                    'WEBP',
                    quality=self.config.webp_quality,
                    method=6)  # Maximum compression

    def _convert_avif_sync(self, original_path: Path, avif_path: Path):
        """Synchronous AVIF conversion (runs in thread pool)"""
        if not AVIF_SUPPORT:
            raise RuntimeError("AVIF support not available - pillow-heif not installed")
            
        with Image.open(original_path) as img:
            # Convert to RGB if necessary
            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGBA')
            elif img.mode != 'RGB':
                img = img.convert('RGB')

            # Save as AVIF using pillow-heif
            img.save(avif_path,
                    'AVIF',
                    quality=self.config.avif_quality,
                    method=6)  # Maximum compression

    async def stop(self):
        """Stop workers"""
        logger.info("Stopping image converter workers")
        self.running = False

        # Signal stop to all workers
        for _ in self.workers:
            await self.queue.put(None)

        # Wait for current tasks to finish
        await self.queue.join()
