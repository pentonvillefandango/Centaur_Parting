from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Where the database file will live
PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DB_PATH = PROJECT_ROOT / "cp_data.db"

DATABASE_URL = f"sqlite:///{DEFAULT_DB_PATH}"

# SQLAlchemy setup
engine = create_engine(
    DATABASE_URL,
    echo=False,      # Set to True for verbose SQL output (debugging)
    future=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    future=True,
)

Base = declarative_base()


@contextmanager
def get_session() -> Iterator["Session"]:
    """
    Provides a database session in a safe way.
    Usage:

    with get_session() as session:
        session.add(...)
        session.commit()
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db() -> None:
    """
    Creates all tables defined in the models.
    Will run later when we add models.
    """
    from centaur.db import models  # This ensures models are imported
    Base.metadata.create_all(bind=engine)

