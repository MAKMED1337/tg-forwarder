import asyncio
import logging
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime, timedelta


class Batcher[T]:
    def __init__(self, func: Callable[[list[T]], Awaitable[None]], logger: logging.Logger | None = None) -> None:
        self._func = func
        self._buffer: list[tuple[T, datetime]] = []
        # This is probably not needed, cause operations on list are not blocking,
        # however I am not sure what will happen with GIL removal
        self._lock = asyncio.Lock()
        self._waiters: set[asyncio.Task] = set()
        self._logger = logger or logging.getLogger(__name__)

    async def process_batch(self) -> None:
        async with self._lock:
            if not self._buffer:
                return

            batch = self._buffer.copy()
            self._buffer.clear()

        await self._func([i for i, _ in batch])

    def schedule_processing(self, delay: timedelta) -> None:
        async def wait_and_process(delay: timedelta) -> None:
            await asyncio.sleep(delay.total_seconds())
            finished = datetime.now(tz=UTC)

            async with self._lock:
                if not self._buffer or max(received for _, received in self._buffer) > finished + delay:
                    self._logger.info(
                        'Scheduled processing skipped, finished time: %s, buffer: %s', finished, self._buffer
                    )
                    return

            await self.process_batch()

        task = asyncio.create_task(wait_and_process(delay))
        self._waiters.add(task)
        task.add_done_callback(self._waiters.discard)

    async def append(self, data: T, when: datetime | None = None) -> None:
        if when is None:
            when = datetime.now(tz=UTC)

        async with self._lock:
            self._buffer.append((data, when))
