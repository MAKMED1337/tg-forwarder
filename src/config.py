from pathlib import Path

from pydantic import BaseModel, Field, TypeAdapter


class Forward(BaseModel):
    from_: str = Field(alias='from')
    to: str


class Config(BaseModel):
    debounce_time_ms: int
    forwards: list[Forward]


def load_config(path: Path = Path('.env/forward.json')) -> Config:
    ta = TypeAdapter(Config)
    return ta.validate_json(path.read_bytes(), strict=True)
