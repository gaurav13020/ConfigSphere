from __future__ import annotations

import os
from typing import Generator

import redis
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker


DATABASE_URL = (
    f"postgresql+psycopg://{os.getenv('POSTGRES_USER', 'postgres')}:"
    f"{os.getenv('POSTGRES_PASSWORD', 'postgres')}@"
    f"{os.getenv('POSTGRES_HOST', 'postgres')}:"
    f"{os.getenv('POSTGRES_PORT', '5432')}/"
    f"{os.getenv('POSTGRES_DB', 'configsphere_v2')}"
)

engine = create_engine(
    DATABASE_URL,
    future=True,
    pool_size=int(os.getenv("SQLALCHEMY_POOL_SIZE", "30")),
    max_overflow=int(os.getenv("SQLALCHEMY_MAX_OVERFLOW", "60")),
    pool_timeout=int(os.getenv("SQLALCHEMY_POOL_TIMEOUT", "30")),
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


_REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

_redis_pool = redis.ConnectionPool.from_url(
    _REDIS_URL,
    max_connections=50,
    decode_responses=True,
)


def get_redis_client() -> redis.Redis:
    return redis.Redis(connection_pool=_redis_pool)
