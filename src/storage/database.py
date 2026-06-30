"""SQLite database connection and initialization."""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from sqlmodel import Session, SQLModel, create_engine

# Import models so they register in SQLModel.metadata before create_all
import src.storage.models  # noqa: F401

# Cache engines per database path
_engines: dict[str, any] = {}


def _get_engine(db_path: Path):
    """Get or create a SQLAlchemy engine for the given database path."""
    path_str = str(db_path)
    if path_str not in _engines:
        url = f"sqlite:///{path_str}"
        _engines[path_str] = create_engine(url, echo=False)
    return _engines[path_str]


def init_db(db_path: Path) -> None:
    """Initialize the database, creating tables if they don't exist.

    Args:
        db_path: Path to the SQLite database file.
    """
    db_path.parent.mkdir(parents=True, exist_ok=True)
    engine = _get_engine(db_path)
    SQLModel.metadata.create_all(engine)


@contextmanager
def get_session(db_path: Path) -> Generator[Session, None, None]:
    """Get a database session as a context manager.

    Args:
        db_path: Path to the SQLite database file.

    Yields:
        A SQLModel Session.
    """
    engine = _get_engine(db_path)
    with Session(engine) as session:
        yield session
