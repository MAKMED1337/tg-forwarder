import asyncio
import functools
import logging
import signal
from datetime import timedelta
from typing import TYPE_CHECKING

from telethon.events import NewMessage

from bot import bot
from bot import start as start_bot
from config import load_config
from helper import create_logger
from logic import Batcher

if TYPE_CHECKING:
    from telethon.tl.types import Channel

shutting_down = asyncio.Event()


config = load_config()


channel_batchers: dict[str, Batcher] = {}


async def process_events(from_: str, events: list[NewMessage.Event]) -> None:
    logger = logging.getLogger(from_)

    ids = [event.id for event in events]
    logger.info('Processing batch for: %s', ids)
    to = [i.to for i in config.forwards if i.from_ == from_]

    for username in to:
        logger.info('Forwarding to %s', username)
        await bot.forward_messages(username, ids, from_)


def get_batcher(username: str) -> Batcher:
    if batcher := channel_batchers.get(username):
        return batcher

    logger = logging.getLogger(username)
    func = functools.partial(process_events, username)
    ret = channel_batchers[username] = Batcher(func, logger)
    return ret


@bot.on(NewMessage(incoming=True))
async def handle(event: NewMessage.Event) -> None:
    chat: Channel = await event.get_chat()

    source = chat.username
    if source is None or source not in (i.from_ for i in config.forwards):
        return

    logging.getLogger(source).info('New message')
    if shutting_down.is_set():
        return

    batcher = get_batcher(source)
    await batcher.append(event)
    batcher.schedule_processing(delay=timedelta(milliseconds=config.debounce_time_ms))


def setup_signals(loop: asyncio.AbstractEventLoop) -> None:
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(shutdown()))


async def shutdown() -> None:
    if shutting_down.is_set():
        return

    logging.getLogger('main').info('Shutdown')
    shutting_down.set()

    for batcher in channel_batchers.values():
        await batcher.process_batch()
    await bot.disconnect()


async def main() -> None:
    datefmt = '%d.%m.%Y %H:%M:%S'
    logger = create_logger(
        'main', format='[%(asctime)s] %(levelname)s: %(message)s', level=logging.INFO, datefmt=datefmt
    )
    logger.setLevel(logging.INFO)

    # Config loggers to print corresponding from username
    for forward_config in config.forwards:
        # We can configure the same logger multiple times, but it should not do any harm
        create_logger(
            forward_config.from_,
            level=logging.INFO,
            format=f'[%(asctime)s] [@{forward_config.from_}] %(levelname)s: %(message)s',
            datefmt=datefmt,
        )

    loop = asyncio.get_running_loop()
    setup_signals(loop)

    logger.info('Start')

    await start_bot()
    await bot.run_until_disconnected()


if __name__ == '__main__':
    asyncio.run(main())
