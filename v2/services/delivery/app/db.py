from __future__ import annotations

import os
from typing import Generator

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
