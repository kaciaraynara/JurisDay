import os
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
import google.genai as genai

from backend_api.db import obter_db
from backend_api import models
from backend_api.routers.auth import get_current_advogado

router = APIRouter()

class ClienteCreate(BaseModel):
    nome: str
    cpf_cnpj: str | None = None
    email: str | None = None
    whatsapp: str
    endereco: str | None = None
    numero_processo: str
    tribunal: str | None = None


class AndamentoUpdate(BaseModel):
    cliente_id: int
    andamento: str


class MensagemRequest(BaseModel):
    cliente_id: int
    tom: str | None = None


@router.post("/cadastrar")
def cadastrar_cliente(
    cliente: ClienteCreate,
    db: Session = Depends(obter_db),
    usuario=Depends(get_current_advogado),
):
    adv = db.query(models.Advogado).filter(models.Advogado.id == usuario.id).first()
    if not adv:
        raise HTTPException(status_code=404, detail="Advogado não encontrado")
    novo = models.Cliente(
        nome=cliente.nome,
        cpf_cnpj=cliente.cpf_cnpj,
        email=cliente.email,
        whatsapp=cliente.whatsapp,
        endereco=cliente.endereco,
        numero_processo=cliente.numero_processo,
        tribunal=cliente.tribunal,
        advogado=adv,
    )
    db.add(novo)
    db.commit()
    db.refresh(novo)
    return {"ok": True, "id": novo.id}


@router.post("/atualizar-andamento")
def atualizar_andamento(
    payload: AndamentoUpdate,
    db: Session = Depends(obter_db),
    usuario=Depends(get_current_advogado),
):
    cliente = db.query(models.Cliente).filter(
        models.Cliente.id == payload.cliente_id,
        models.Cliente.advogado_id == usuario.id,
    ).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    cliente.andamento_atual = payload.andamento
    cliente.ultima_atualizacao = datetime.now(timezone.utc)
    db.commit()
    return {"ok": True, "cliente_id": cliente.id}


def _gerar_mensagem(cliente: models.Cliente, tom: str | None):
    chave = os.getenv("GOOGLE_GENAI_KEY") or os.getenv("GENAI_KEY")
    if not chave:
        return (
            f"Olá {cliente.nome}, atualização do seu processo {cliente.numero_processo}: "
            f"{cliente.andamento_atual or 'há uma movimentação recente'}. "
            "Se precisar de algo, estou à disposição."
        )
    try:
        client = genai.Client(api_key=chave)
        prompt = (
            "Você é um advogado escrevendo uma atualização curta e clara para o cliente. "
            "Explique o andamento em linguagem simples e respeitosa. "
            f"Tom: {tom or 'profissional e humano'}. "
            f"Cliente: {cliente.nome}. "
            f"Processo: {cliente.numero_processo}. "
            f"Andamento informado pelo advogado: {cliente.andamento_atual}."
        )
        resp = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
        return resp.text
    except Exception:
        return (
            f"Olá {cliente.nome}, atualização do seu processo {cliente.numero_processo}: "
            f"{cliente.andamento_atual or 'há uma movimentação recente'}. "
            "Qualquer dúvida, estou à disposição."
        )


@router.post("/gerar-mensagem")
def gerar_mensagem(
    payload: MensagemRequest,
    db: Session = Depends(obter_db),
    usuario=Depends(get_current_advogado),
):
    cliente = db.query(models.Cliente).filter(
        models.Cliente.id == payload.cliente_id,
        models.Cliente.advogado_id == usuario.id,
    ).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    if not cliente.andamento_atual:
        raise HTTPException(status_code=400, detail="Informe o andamento antes de gerar a mensagem")
    texto = _gerar_mensagem(cliente, payload.tom)
    return {"mensagem": texto}


@router.get("/listar")
def listar_clientes(
    db: Session = Depends(obter_db),
    usuario=Depends(get_current_advogado),
):
    clientes = db.query(models.Cliente).filter(models.Cliente.advogado_id == usuario.id).all()
    return {"clientes": [
        {
            "nome": c.nome,
            "cpf_cnpj": c.cpf_cnpj,
            "email": c.email,
            "whatsapp": c.whatsapp,
            "endereco": c.endereco,
            "numero_processo": c.numero_processo,
            "tribunal": c.tribunal,
            "andamento_atual": c.andamento_atual,
            "ultima_atualizacao": c.ultima_atualizacao.isoformat() if c.ultima_atualizacao else None,
            "id": c.id,
        } for c in clientes
    ]}
