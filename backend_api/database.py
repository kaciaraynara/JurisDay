from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Conexão com o banco de dados local
URL_BANCO_DADOS = "sqlite:///./jurisday_producao.db"

engine = create_engine(
    URL_BANCO_DADOS, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def obter_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()