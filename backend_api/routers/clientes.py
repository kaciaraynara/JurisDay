from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend_api.db import obter_db
import backend_api.models as models
from backend_api.routers.auth import get_current_advogado

router = APIRouter()

class ClienteCreate(BaseModel):
    nome: str
    cpf_cnpj: str
    email: str
    whatsapp: str
    numero_processo: str
    tribunal: str


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
        numero_processo=cliente.numero_processo,
        tribunal=cliente.tribunal,
        advogado=adv,
    )
    db.add(novo)
    db.commit()
    db.refresh(novo)
    return {"ok": True, "id": novo.id}


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
            "numero_processo": c.numero_processo,
            "tribunal": c.tribunal,
        } for c in clientes
    ]}
