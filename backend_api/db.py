import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.engine.url import make_url
from sqlalchemy.orm import sessionmaker, declarative_base

# --- Resolve DATABASE_URL com caminho estável e cria a pasta se usar SQLite ---
def _resolve_database_url():
    env_url = os.getenv("DATABASE_URL")
    if env_url:
        url_obj = make_url(env_url)
    else:
        base_dir = Path(__file__).resolve().parent
        default_path = base_dir / "data" / "app.db"
        default_path.parent.mkdir(parents=True, exist_ok=True)
        url_obj = make_url(f"sqlite:///{default_path}")

    if url_obj.drivername == "sqlite":
        db_path = Path(url_obj.database or "")
        if not db_path.is_absolute():
            db_path = Path.cwd() / db_path
        db_path.parent.mkdir(parents=True, exist_ok=True)
        url_obj = url_obj.set(database=str(db_path))
    return str(url_obj)


DATABASE_URL = _resolve_database_url()
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine_kwargs = {
    "pool_pre_ping": True,
    "connect_args": connect_args,
}
if not DATABASE_URL.startswith("sqlite"):
    engine_kwargs.update({"pool_size": 10, "max_overflow": 20})

engine = create_engine(DATABASE_URL, **engine_kwargs)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def obter_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
