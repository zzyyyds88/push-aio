from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


# src/pushhub/core/db.py → parents[3] = 项目根目录
BASE_DIR = Path(__file__).resolve().parents[3]
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DATABASE_URL = f"sqlite:///{(DATA_DIR / 'pushhub.db').as_posix()}"

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


# 说明：本程序未实际部署，不引入 alembic 等迁移框架。
# 表结构变更时，Base.metadata.create_all 只能创建缺失的表，不会改已存在的表。
# 为避免删除 data/pushhub.db 丢失历史日志，启动时直接对现有库做 ALTER TABLE 兜底：
# 缺什么列就补什么列；已存在则跳过。
def ensure_schema() -> None:
    """启动时直接对现有 SQLite 库补列，保留历史数据。

    每条 ALTER 都是幂等的（先 inspect 列名再决定是否执行）。
    新增字段时在这里追加一条分支即可，无需写迁移文件。
    """
    inspector = inspect(engine)
    if "delivery_logs" not in inspector.get_table_names():
        return  # 表还没建，create_all 会按最新模型建

    existing_columns = {col["name"] for col in inspector.get_columns("delivery_logs")}
    with engine.begin() as conn:
        if "error_kind" not in existing_columns:
            # 历史日志没有错误分类，统一记为 none（表示未分类）
            conn.execute(
                text(
                    "ALTER TABLE delivery_logs ADD COLUMN error_kind VARCHAR(20) "
                    "NOT NULL DEFAULT 'none'"
                )
            )


# 说明：本程序未实际部署，禁止写迁移机制。
# 表结构变更时，请手动删除 data/pushhub.db 后重启服务，Base.metadata.create_all 会按最新模型重建。
# 例外：为保留历史日志（用户偏好：日志永久保留、禁止数据丢失），新增列通过 ensure_schema() 直接 ALTER。
