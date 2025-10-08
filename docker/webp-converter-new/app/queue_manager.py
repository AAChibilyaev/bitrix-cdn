"""
Queue management with rate limiting
"""
import asyncio
from collections import deque
from datetime import datetime
from app.metrics import metrics
import structlog

logger = structlog.get_logger()

class QueueManager:
    def __init__(self, config):
        self.config = config
        self.queue = asyncio.Queue(maxsize=config.max_queue_size)
        # Rate limiter: max files per minute
        self.rate_limiter = asyncio.Semaphore(config.rate_limit)
        self._reset_limiter_task = None

        # Track processing history (last 100 items)
        self.processing_history = deque(maxlen=100)
        self.completed_history = deque(maxlen=100)

        # Current processing items
        self.currently_processing = {}

        # Statistics
        self.stats = {
            'total_processed': 0,
            'total_errors': 0,
            'total_skipped': 0,
            'start_time': datetime.now()
        }

    async def put(self, item: str):
        """Add item to queue with rate limiting"""
        async with self.rate_limiter:
            await self.queue.put(item)
            metrics.queue_size.set(self.queue.qsize())
            logger.debug("Item added to queue",
                        queue_size=self.queue.qsize())

    async def get(self):
        """Get item from queue"""
        item = await self.queue.get()
        metrics.queue_size.set(self.queue.qsize())
        return item

    def task_done(self):
        """Mark task as complete"""
        self.queue.task_done()

    async def join(self):
        """Wait for all tasks to complete"""
        await self.queue.join()

    def qsize(self):
        """Current queue size"""
        return self.queue.qsize()

    def mark_processing(self, worker_id: int, file_path: str):
        """Mark item as currently processing"""
        self.currently_processing[worker_id] = {
            'file': file_path,
            'started_at': datetime.now().isoformat()
        }

    def mark_completed(self, worker_id: int, file_path: str, status: str, duration: float = None, error: str = None):
        """Mark item as completed"""
        if worker_id in self.currently_processing:
            del self.currently_processing[worker_id]

        completed = {
            'file': file_path,
            'status': status,
            'completed_at': datetime.now().isoformat(),
            'duration': duration,
            'error': error
        }
        self.completed_history.append(completed)

        if status == 'success':
            self.stats['total_processed'] += 1
        elif status == 'error':
            self.stats['total_errors'] += 1
        elif status == 'skipped':
            self.stats['total_skipped'] += 1

    def get_status(self):
        """Get detailed queue status"""
        uptime = (datetime.now() - self.stats['start_time']).total_seconds()

        # Get queue items (pending)
        pending_items = []
        temp_items = []
        while not self.queue.empty():
            try:
                item = self.queue.get_nowait()
                temp_items.append(item)
                pending_items.append(item)
            except asyncio.QueueEmpty:
                break

        # Put items back
        for item in temp_items:
            try:
                self.queue.put_nowait(item)
            except asyncio.QueueFull:
                break

        return {
            'queue': {
                'pending': pending_items[:10],  # First 10 pending
                'pending_count': len(pending_items),
                'max_size': self.config.max_queue_size
            },
            'processing': {
                'current': list(self.currently_processing.values()),
                'count': len(self.currently_processing)
            },
            'completed': {
                'recent': list(self.completed_history)[:10],  # Last 10 completed
                'total': self.stats['total_processed']
            },
            'stats': {
                'total_processed': self.stats['total_processed'],
                'total_errors': self.stats['total_errors'],
                'total_skipped': self.stats['total_skipped'],
                'uptime_seconds': uptime,
                'processing_rate': self.stats['total_processed'] / uptime if uptime > 0 else 0
            }
        }

    async def start_rate_limiter_reset(self):
        """Reset rate limiter every minute"""
        while True:
            await asyncio.sleep(60)  # 1 minute
            # Release all permits to reset the rate limit
            for _ in range(self.config.rate_limit):
                try:
                    self.rate_limiter.release()
                except ValueError:
                    break
            logger.debug("Rate limiter reset")
