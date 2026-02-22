import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    db_host: str
    db_port: str
    db_name: str
    db_user: str
    db_password: str
    database_url: str | None
    pool_min_size: int
    pool_max_size: int


def _get_int_env(name: str, default: int) -> int:
    value = os.getenv(name)
    if not value:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def get_settings() -> Settings:
    return Settings(
        db_host=os.getenv("PGHOST", "localhost"),
        db_port=os.getenv("PGPORT", "5432"),
        db_name=os.getenv("PGDATABASE", "travel"),
        db_user=os.getenv("PGUSER", "postgres"),
        db_password=os.getenv("PGPASSWORD", "postgres"),
        database_url=os.getenv("DATABASE_URL"),
        pool_min_size=_get_int_env("PGPOOL_MIN", 1),
        pool_max_size=_get_int_env("PGPOOL_MAX", 10),
    )


def build_conninfo(settings: Settings) -> str:
    if settings.database_url:
        return settings.database_url
    return (
        f"postgresql://{settings.db_user}:{settings.db_password}"
        f"@{settings.db_host}:{settings.db_port}/{settings.db_name}"
    )
