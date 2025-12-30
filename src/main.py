import asyncio
import logging
import signal
from datetime import UTC, datetime, timedelta

from telethon.events import NewMessage

from bot import bot
from bot import start as start_bot
from config import forward_settings

shutting_down = asyncio.Event()


events_buffer: list[tuple[NewMessage.Event, datetime]] = []
events_lock = asyncio.Lock()
background_tasks: set[asyncio.Task] = set()


logger = logging.getLogger('main')


async def process_batch() -> None:
    async with events_lock:
        if not events_buffer:
            return

        batch = events_buffer.copy()
        events_buffer.clear()

    ids = [event.id for event, _ in batch]
    logger.info('Processing batch: %s', ids)
    await bot.forward_messages(forward_settings.to, ids, forward_settings.from_)


async def schedule_processing(delay: timedelta) -> None:
    async def wait_and_process(delay: timedelta) -> None:
        await asyncio.sleep(delay.total_seconds())
        finished = datetime.now(tz=UTC)

        async with events_lock:
            if not events_buffer or max(received for _, received in events_buffer) > finished + delay:
                logger.info('Scheduled processing skipped, finished time: %s, buffer: %s', finished, events_buffer)
                return

        await process_batch()

    task = asyncio.create_task(wait_and_process(delay))
    background_tasks.add(task)
    task.add_done_callback(background_tasks.discard)


@bot.on(NewMessage(chats=[forward_settings.from_]))
async def handle(event: NewMessage.Event) -> None:
    logger.info('New message')
    if shutting_down.is_set():
        return

    async with events_lock:
        events_buffer.append((event, datetime.now(tz=UTC)))
    await schedule_processing(delay=timedelta(milliseconds=forward_settings.debounce_time_ms))


def setup_signals(loop: asyncio.AbstractEventLoop) -> None:
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(shutdown()))


async def shutdown() -> None:
    if shutting_down.is_set():
        return

    logger.info('Shutdown')
    shutting_down.set()

    await process_batch()
    await bot.disconnect()


async def main() -> None:
    logging.basicConfig(format='[%(asctime)s] %(levelname)s: %(message)s', datefmt='%d.%m.%Y %H:%M:%S')

    logger.setLevel(logging.INFO)

    loop = asyncio.get_running_loop()
    setup_signals(loop)

    logger.info('Start')
    await start_bot()
    await bot.run_until_disconnected()


if __name__ == '__main__':
    asyncio.run(main())
