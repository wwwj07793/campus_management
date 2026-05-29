from contextlib import contextmanager
from typing import Iterator

from config import SessionLocal, engine
from core.models.base import Base


def init_db() -> None:
    import core.models.mysqlDB  # noqa: F401

    Base.metadata.create_all(bind=engine)


@contextmanager
def session_scope() -> Iterator:
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
