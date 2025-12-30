from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ForwardSetting(BaseSettings):
    model_config = SettingsConfigDict(case_sensitive=False)

    from_: str = Field(alias='from')  # should be a username, not an id
    to: str  # should be a username, not an id
    debounce_time_ms: int


forward_settings = ForwardSetting()  # type: ignore[call-arg]
