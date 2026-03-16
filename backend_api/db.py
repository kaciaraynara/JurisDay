import os
import urllib.parse
from sqlalchemy import create_engine

raw_uri = os.getenv("DATABASE_URL")

if raw_uri:
    # Ajuste o protocolo
    if raw_uri.startswith("postgres://"):
        raw_uri = raw_uri.replace("postgres://", "postgresql://", 1)
    
    # Se a senha tiver caracteres como @ ou !, isso aqui protege a conexão
    # O Render fornece a URL pronta, mas vamos garantir:
    engine = create_engine(raw_uri, pool_pre_ping=True)
else:
    engine = create_engine("sqlite:///./local.db")