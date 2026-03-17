from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend_api.db import Base
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

    # Relacionamentos Profissionais
    processos = relationship("Processo", back_populates="advogado")
    clientes = relationship("Cliente", back_populates="advogado")

class Cliente(Base):
    __tablename__ = "clientes"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    cpf_cnpj = Column(String, index=True, nullable=True)
    email = Column(String, nullable=True)
    whatsapp = Column(String, nullable=True)
    endereco = Column(String, nullable=True)
    numero_processo = Column(String, nullable=True)
    tribunal = Column(String, nullable=True)
    andamento_atual = Column(Text, nullable=True)
    ultima_atualizacao = Column(DateTime, nullable=True)
    advogado_id = Column(Integer, ForeignKey("advogados.id"))

    advogado = relationship("Advogado", back_populates="clientes")
    processos = relationship("Processo", back_populates="cliente")

class Processo(Base):
    __tablename__ = "processos"

    id = Column(Integer, primary_key=True, index=True)
    numero = Column(String, index=True, nullable=False)
    tribunal = Column(String)
    parte_contraria = Column(String, nullable=True)
    parte = Column(String, nullable=True)
    telefone_cliente = Column(String, nullable=True)
    referencia = Column(String, nullable=True)
    status = Column(String, default="Ativo")
    ultimo_andamento = Column(Text)
    
    advogado_id = Column(Integer, ForeignKey("advogados.id"))
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=True)

    advogado = relationship("Advogado", back_populates="processos")
    cliente = relationship("Cliente", back_populates="processos")
