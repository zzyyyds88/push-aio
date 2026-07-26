from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


# src/push_aio/core/db.py → parents[3] = 项目根目录
BASE_DIR = Path(__file__).resolve().parents[3]
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DATABASE_URL = f"sqlite:///{(DATA_DIR / 'push_aio.db').as_posix()}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def session_scope():
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# 说明：本程序未实际部署，禁止写迁移机制。
# 表结构变更时，请手动删除 data/push_aio.db 后重启服务，Base.metadata.create_all 会按最新模型重建。
