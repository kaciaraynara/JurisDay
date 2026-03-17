import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# ... (restante do seu código)

# 1. Sirva os arquivos da pasta frontend (CSS, JS, Imagens)
# Certifique-se de que o nome da pasta no seu projeto é 'frontend'
app.mount("/static", StaticFiles(directory="frontend"), name="static")

# 2. Rota para servir o index.html na raiz
@app.get("/")
async def read_index():
    return FileResponse('frontend/index.html')

SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

if SQLALCHEMY_DATABASE_URL and SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(SQLALCHEMY_DATABASE_URL or "sqlite:///./local.db")

# O NOME PRECISA SER ESTE:
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
# Adicione isso ao final do seu db.py
def obter_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()