import logging

from sqlalchemy import create_engine, event
from sqlalchemy.engine.url import make_url
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from .config import settings

logger = logging.getLogger("app.database")
logging.basicConfig(level=logging.INFO)


class Base(DeclarativeBase):
    """Base declarative class."""


# 打印当前使用的数据库连接（隐藏密码），并开启 SQL 回显
_db_url = make_url(settings.database_url)
logger.info("Using database: %s", _db_url.render_as_string(hide_password=True))

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    future=True,
    echo=False,  # 关闭全量 echo，改为自定义精简日志
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)


@event.listens_for(engine, "after_cursor_execute")
def _log_sql(conn, cursor, statement, parameters, context, executemany) -> None:
    """仅打印业务 SQL，过滤掉模式探测等噪声。"""
    stmt_upper = statement.strip().upper()
    noisy_prefixes = (
        "SELECT DATABASE()",
        "SELECT @@SQL_MODE",
        "SELECT @@LOWER_CASE_TABLE_NAMES",
        "DESCRIBE ",
        "PRAGMA ",
        "SHOW FULL TABLES",
    )
    if any(stmt_upper.startswith(prefix) for prefix in noisy_prefixes):
        return
    logger.info("SQL: %s | params=%s", statement, parameters)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

