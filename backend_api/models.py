from sqlalchemy import Column, Integer, String, Text, DateTime
from db import Base
from datetime import datetime, timezone

class Advogado(Base):
    __tablename__ = "advogados"

    id = Column(Integer, primary_key=True, index=True)
    nome_completo = Column(String, nullable=False)
    cpf_cnpj = Column(String, unique=True, index=True, nullable=False)
    oab = Column(String, nullable=True)
    email = Column(String, unique=True, index=True, nullable=False)
    whatsapp = Column(String, nullable=True)
    senha_hash = Column(String, nullable=False)
    lembrete_senha = Column(String, nullable=True)
    plano_atual = Column(String, default="Trial")
    logo_base64 = Column(Text, nullable=True)
    data_cadastro = Column(DateTime, default=lambda: datetime.now(timezone.utc))