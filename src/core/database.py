from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base
from src.core.config import settings

_connect_args = {}
if settings.DATABASE_URL and settings.DATABASE_URL.startswith("sqlite"):
    _connect_args = {"check_same_thread": False}

# Pool settings to handle Neon's idle connection drops:
# - pool_pre_ping: tests connections before using them (auto-reconnect)
# - pool_recycle: closes connections before Neon's idle timeout
engine = create_engine(
    settings.DATABASE_URL,
    connect_args=_connect_args,
    pool_pre_ping=True,
    pool_recycle=300,
    pool_size=5,
    max_overflow=10,
)

# For PostgreSQL with SSL (Neon), add statement timeout on connect
if settings.DATABASE_URL and "postgresql" in settings.DATABASE_URL:
    @event.listens_for(engine, "connect")
    def _set_pg_keepalive(dbapi_conn, connection_record):
        try:
            cursor = dbapi_conn.cursor()
            cursor.execute("SET statement_timeout = 30000")
            cursor.close()
        except Exception:
            pass

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
