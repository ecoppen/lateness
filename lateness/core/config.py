import json
from datetime import time
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Extra, Field, HttpUrl, ValidationError


class Databases(Enum):
    POSTGRES = "postgres"
    SQLITE = "sqlite"


class Database(BaseModel, use_enum_values=True, extra=Extra.forbid):  # type: ignore
    engine: str = Databases.SQLITE  # type: ignore
    username: Optional[str]
    password: Optional[str]
    host: Optional[HttpUrl] = "127.0.0.1"  # type: ignore
    port: Optional[int] = Field(5432, ge=1, le=65535)
    name: str = "db_lateness"


class Config(BaseModel, extra=Extra.forbid):  # type: ignore
    database: Database
    api_get: HttpUrl = "10.192.41.212"  # type: ignore
    start_time: time = time(hour=8, minute=40)
    end_time: time = time(hour=14, minute=40)


def load_config(path):
    if not path.is_file():
        raise ValueError(f"{path} does not exist")
    else:
        f = open(path)
        try:
            data = json.load(f)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"ERROR: Invalid JSON: {exc.msg}, line {exc.lineno}, column {exc.colno}"
            )

        try:
            return Config(**data)
        except ValidationError as e:
            raise ValueError(f"{e}")
