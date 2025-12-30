from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict
from telethon import TelegramClient


class UserSettings(BaseSettings):
    model_config = SettingsConfigDict(case_sensitive=False)

    api_hash: str
    api_id: int
    bot_token: str | None = None


_settings = UserSettings()  # type: ignore[call-arg]

bot = TelegramClient(
    Path('.sessions/bot'),
    _settings.api_id,
    _settings.api_hash,
    sequential_updates=True,
    catch_up=True,
)
bot.parse_mode = 'html'


async def start() -> None:
    await bot.start(bot_token=_settings.bot_token)  # type: ignore[misc]
    await bot.catch_up()
