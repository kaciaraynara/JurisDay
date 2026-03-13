from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship

# Compatível tanto com execução como pacote quanto rodando de dentro da pasta backend_api
try:
    from .db import Base  # tipo pacote
except ImportError:
    from db import Base  # execução direta a partir da pasta backend_api

class Advogado(Base):
    __tablename__ = "advogados"
    id = Column(Integer, primary_key=True, index=True)
    nome_completo = Column(String)
    cpf_cnpj = Column(String, unique=True, index=True)
    oab = Column(String, nullable=True)
    email = Column(String, unique=True, index=True)
    senha_hash = Column(String)
    plano_atual = Column(String, default="Trial")
    whatsapp = Column(String, nullable=True)
    logo_base64 = Column(Text, nullable=True)
    clientes = relationship("Cliente", back_populates="advogado")

class Cliente(Base):
    __tablename__ = "clientes"
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String)
    cpf_cnpj = Column(String)
    email = Column(String)
    whatsapp = Column(String)
    numero_processo = Column(String)
    tribunal = Column(String)
    advogado_id = Column(Integer, ForeignKey("advogados.id"))
    advogado = relationship("Advogado", back_populates="clientes")

class Processo(Base):
    __tablename__ = "processos"
    id = Column(Integer, primary_key=True, index=True)
    numero = Column(String, index=True)
    tribunal = Column(String, index=True)
    parte = Column(String)
    telefone_cliente = Column(String)
    referencia = Column(String)
    status = Column(String, default="pendente")
    ultimo_andamento = Column(Text, default="")
