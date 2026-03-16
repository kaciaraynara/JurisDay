import os
import requests
from typing import List, Dict
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# IMPORTAÇÃO LIMPA PARA O RENDER
from db import SessionLocal, engine
import models
from models import Processo
from routers.auth import get_current_advogado

# models.Base.metadata.create_all(bind=engine)

# models.Base.metadata.create_all(bind=engine)

router = APIRouter()

JUS_API_URL = os.getenv("JUS_API_URL", "https://api.jusplaceholder.local")
JUS_API_TOKEN = os.getenv("JUS_API_TOKEN", "")
WHATSAPP_WEBHOOK_URL = os.getenv("WHATSAPP_WEBHOOK_URL")
MONITOR_INTERVAL_MINUTES = int(os.getenv("MONITOR_INTERVAL_MINUTES", "1440"))

scheduler = AsyncIOScheduler(timezone="UTC")
SCHEDULER_JOB_ID = "monitor-diario"


class ProcessoSchema(BaseModel):
    numero: str
    tribunal: str
    parte: str
    telefone_cliente: str | None = None
    referencia: str | None = None


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def consultar_processo(proc: Processo) -> Dict:
    headers = {"Authorization": f"Bearer {JUS_API_TOKEN}"} if JUS_API_TOKEN else {}
    try:
        resp = requests.get(
            f"{JUS_API_URL}/processos/{proc.numero}",
            headers=headers,
            timeout=10,
            params={"tribunal": proc.tribunal},
        )
        if resp.status_code != 200:
            return {"status": f"erro http {resp.status_code}"}
        data = resp.json()
        return {
            "status": data.get("status", "desconhecido"),
            "ultimo_andamento": data.get("andamento", "sem movimentação"),
        }
    except Exception as e:
        return {"status": f"falha consulta: {e}"}


def _formatar_resumo(lista: List[Processo]) -> str:
    if not lista:
        return "Nenhum processo monitorado no momento."
    linhas = ["Resumo diário dos seus processos:\n"]
    for p in lista:
        linhas.append(
            f"- Proc. {p.numero} ({p.tribunal}), parte {p.parte}: status {p.status or 'pendente'}. "
            f"Último andamento: {p.ultimo_andamento or 'sem movimentação'}."
        )
    linhas.append("\nTradução humana: seguimos atentos; qualquer prazo será avisado.")
    return "\n".join(linhas)


def _enviar_whatsapp(texto: str, telefone: str | None):
    if not WHATSAPP_WEBHOOK_URL or not telefone:
        return {"enviado": False, "motivo": "webhook/telefone ausente", "mensagem": texto}
    try:
        r = requests.post(WHATSAPP_WEBHOOK_URL, json={"to": telefone, "message": texto}, timeout=10)
        return {"enviado": r.status_code == 200, "status_code": r.status_code, "mensagem": texto}
    except Exception as e:
        return {"enviado": False, "motivo": str(e), "mensagem": texto}


def _monitorar_once(db: Session):
    processos = db.query(Processo).all()
    for p in processos:
        res = consultar_processo(p)
        p.status = res.get("status")
        p.ultimo_andamento = res.get("ultimo_andamento")
    db.commit()
    return processos


def _serialize(proc: Processo) -> Dict:
    return {
        "numero": proc.numero,
        "tribunal": proc.tribunal,
        "parte": proc.parte,
        "telefone_cliente": proc.telefone_cliente,
        "referencia": proc.referencia,
        "status": proc.status,
        "ultimo_andamento": proc.ultimo_andamento,
    }


def _agendar_monitoramento():
    def _job():
        db = SessionLocal()
        try:
            _monitorar_once(db)
        finally:
            db.close()
    scheduler.add_job(
        _job,
        "interval",
        minutes=MONITOR_INTERVAL_MINUTES,
        id=SCHEDULER_JOB_ID,
        replace_existing=True,
    )


def ensure_scheduler_started():
    if not scheduler.running:
        _agendar_monitoramento()
        scheduler.start()
    elif not scheduler.get_job(SCHEDULER_JOB_ID):
        _agendar_monitoramento()


def shutdown_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)


@router.post("/registrar")
async def registrar(proc: ProcessoSchema, db: Session = Depends(get_db), usuario=Depends(get_current_advogado)):
    novo = Processo(**proc.model_dump())
    db.add(novo)
    db.commit()
    db.refresh(novo)
    total = db.query(Processo).count()
    return {"ok": True, "total_monitorados": total}


@router.get("/status")
async def status(db: Session = Depends(get_db), usuario=Depends(get_current_advogado)):
    return {"processos": [_serialize(p) for p in db.query(Processo).all()]}


@router.post("/rodar")
async def rodar_agora(db: Session = Depends(get_db), usuario=Depends(get_current_advogado)):
    atualizados = _monitorar_once(db)
    return {"processos": [_serialize(p) for p in atualizados]}


@router.post("/resumo")
async def resumo_whatsapp(db: Session = Depends(get_db), usuario=Depends(get_current_advogado)):
    lista = db.query(Processo).all()
    texto = _formatar_resumo(lista)
    respostas = [_enviar_whatsapp(texto, p.telefone_cliente) for p in lista]
    return {"mensagem": texto, "envios": respostas}


@router.get("/health")
async def health():
    return {"scheduler_running": scheduler.running, "interval_minutes": MONITOR_INTERVAL_MINUTES}
