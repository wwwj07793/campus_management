from __future__ import annotations

import os
from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


def _bool_env(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _csv_env(name: str, default: list[str]) -> list[str]:
    value = os.getenv(name)
    if not value:
        return default
    return [item.strip() for item in value.split(",") if item.strip()]


def _mysql_url_from_env() -> str:
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "3306")
    user = os.getenv("DB_USER", "root")
    password = os.getenv("DB_PASSWORD", "")
    database = os.getenv("DB_NAME", "campus_db")
    charset = os.getenv("DB_CHARSET", "utf8mb4")
    return f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}?charset={charset}"


DATABASE_URL = os.getenv("DATABASE_URL") or _mysql_url_from_env()
AUTH_SECRET = os.getenv("CAMPUS_AUTH_SECRET", "campus-management-dev-secret")
INIT_DB_ON_STARTUP = _bool_env("INIT_DB_ON_STARTUP", default=False)
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

DEFAULT_CORS_ORIGINS = [
    "http://127.0.0.1:8000",
    "http://localhost:8000",
    "http://127.0.0.1:5173",
    "http://localhost:5173",
]
CORS_ORIGINS = _csv_env("CORS_ORIGINS", DEFAULT_CORS_ORIGINS)


def _engine_kwargs(database_url: str) -> dict:
    if database_url.startswith("sqlite"):
        kwargs = {"connect_args": {"check_same_thread": False}}
        if database_url in {"sqlite://", "sqlite:///:memory:"}:
            kwargs["poolclass"] = StaticPool
        return kwargs
    return {
        "pool_pre_ping": True,
        "pool_size": int(os.getenv("DB_POOL_SIZE", "10")),
        "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "20")),
    }


@lru_cache
def create_app_engine() -> Engine:
    return create_engine(DATABASE_URL, **_engine_kwargs(DATABASE_URL))


engine = create_app_engine()
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False,
)
