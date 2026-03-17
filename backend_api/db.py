import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 1. Configuração da URL de Conexão (Variável de Ambiente do Render ou Local)
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

# Correção automática para o dialeto do PostgreSQL exigido pelo SQLAlchemy 2.0+
if SQLALCHEMY_DATABASE_URL and SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgres://", "postgresql://", 1)

# 2. Criação do Engine com Pool de Conexões para Alta Disponibilidade
# pool_pre_ping: Garante que o sistema recupere conexões perdidas automaticamente
# pool_size e max_overflow: Permitem múltiplos acessos simultâneos sem travar
engine = create_engine(
    SQLALCHEMY_DATABASE_URL or "sqlite:///./jurisday_prod.db",
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)

# 3. Configuração da Fábrica de Sessões e Base Declarativa
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 4. Dependência de Injeção para o FastAPI
# Abre a conexão no início da requisição e garante o fechamento ao final
def obter_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()