import os
import uuid
from datetime import datetime, timedelta, timezone
import requests
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

router = APIRouter()

LOG_PATH = os.getenv("PAGAMENTOS_LOG_PATH", "./data/pagamentos.log")
TRIAL_DIAS = int(os.getenv("TRIAL_DIAS", "7"))
PAGSEGURO_TOKEN = os.getenv("PAGSEGURO_TOKEN")
PAGSEGURO_BASE_URL = os.getenv("PAGSEGURO_BASE_URL", "https://api.pagseguro.com")

_pagamentos_memoria = {}


class CheckoutSchema(BaseModel):
    plano: str = Field(..., description="essencial ou pro")
    valor: float
    metodo: str = Field(..., description="pix|credito|debito")
    nome_titular: str | None = None
    numero_cartao: str | None = None
    validade: str | None = None  # formato MM/AA
    cvv: str | None = None


def _parse_validade(validade: str | None):
    if not validade or "/" not in validade:
        return None, None
    partes = validade.split("/")
    mes = partes[0].zfill(2)
    ano = partes[1]
    if len(ano) == 2:
        ano = "20" + ano
    return mes, ano


def _pagseguro_pix(dados: CheckoutSchema, transacao_id: str):
    if not PAGSEGURO_TOKEN:
        raise HTTPException(status_code=500, detail="PagSeguro não configurado para PIX")
    headers = {
        "Authorization": f"Bearer {PAGSEGURO_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    payload = {
        "reference_id": transacao_id[:18],
        "description": f"Plano {dados.plano}",
        "amount": {"value": int(dados.valor * 100), "currency": "BRL"},
        "payment_method": {"type": "PIX"},
    }
    resp = requests.post(f"{PAGSEGURO_BASE_URL}/charges", json=payload, headers=headers, timeout=20)
    if resp.status_code >= 400:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    data = resp.json()
    qr = data.get("payment_response", {}).get("qr_codes", [{}])[0].get("text", "")
    return {
        "status": data.get("status", "pending"),
        "transacao_id": data.get("id", transacao_id),
        "metodo": "pix",
        "codigo_pix": qr,
        "mensagem": "Use o copia e cola para pagar por PIX (PagSeguro).",
        "trial": True,
        "trial_dias": TRIAL_DIAS,
        "cobrar_em": (datetime.now(timezone.utc) + timedelta(days=TRIAL_DIAS)).date().isoformat(),
    }


def _pagseguro_cartao(dados: CheckoutSchema, transacao_id: str):
    if not PAGSEGURO_TOKEN:
        raise HTTPException(status_code=500, detail="PagSeguro não configurado para cartão")
    if not (dados.nome_titular and dados.numero_cartao and dados.validade and dados.cvv):
        raise HTTPException(status_code=400, detail="Dados do cartão incompletos")

    mes, ano = _parse_validade(dados.validade)
    if not mes or not ano:
        raise HTTPException(status_code=400, detail="Validade do cartão inválida (use MM/AA)")

    headers = {
        "Authorization": f"Bearer {PAGSEGURO_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    payload = {
        "reference_id": transacao_id[:18],
        "description": f"Plano {dados.plano}",
        "amount": {"value": int(dados.valor * 100), "currency": "BRL"},
        "payment_method": {
            "type": "CREDIT_CARD",
            "installments": 1,
            "capture": True,
            "card": {
                "number": dados.numero_cartao.replace(" ", ""),
                "exp_month": mes,
                "exp_year": ano,
                "security_code": dados.cvv,
                "holder": {"name": dados.nome_titular},
            },
        },
    }
    resp = requests.post(f"{PAGSEGURO_BASE_URL}/charges", json=payload, headers=headers, timeout=20)
    if resp.status_code >= 400:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    data = resp.json()
    status = data.get("status", "paid")
    last4 = data.get("payment_response", {}).get("last_four_digits", "")
    return {
        "status": status,
        "transacao_id": data.get("id", transacao_id),
        "metodo": "credito",
        "cartao": f"**** **** **** {last4}" if last4 else None,
        "mensagem": "Pagamento confirmado. Plano liberado.",
        "trial": True,
        "trial_dias": TRIAL_DIAS,
        "cobrar_em": (datetime.now(timezone.utc) + timedelta(days=TRIAL_DIAS)).date().isoformat(),
    }


def _log_event(tipo: str, conteudo: str):
    try:
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now(timezone.utc).isoformat()}] {tipo}: {conteudo}\n")
    except Exception:
        pass


def _pagarme_status(transacao_id: str):
    """Consulta status da transação/charge no Pagar.me."""
    if not PAGARME_API_KEY:
        return None
    headers = {"Authorization": f"Basic {PAGARME_API_KEY}"}
    endpoints = [f"/charges/{transacao_id}", f"/transactions/{transacao_id}"]
    for ep in endpoints:
        try:
            resp = requests.get(f"{PAGARME_BASE_URL}{ep}", headers=headers, timeout=12)
            if resp.status_code == 404:
                continue
            resp.raise_for_status()
            data = resp.json()
            status = data.get("status") or data.get("last_transaction", {}).get("status")
            return {"status": status or "desconhecido", "raw": data}
        except Exception:
            continue
    return None


def _verify_webhook(body: bytes, signature: str | None):
    if not PAGARME_WEBHOOK_SECRET:
        return True  # sem segredo configurado, apenas registra
    if not signature:
        return False
    mac = hmac.new(PAGARME_WEBHOOK_SECRET.encode(), msg=body, digestmod=hashlib.sha256)
    expected = mac.hexdigest()
    # pagar.me costuma enviar "sha256=..." ou apenas hex
    sig_clean = signature.replace("sha256=", "") if signature.startswith("sha256=") else signature
    return hmac.compare_digest(expected, sig_clean)


def _log_event(tipo: str, conteudo: str):
    try:
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now(timezone.utc).isoformat()}] {tipo}: {conteudo}\n")
    except Exception:
        pass


@router.post("/checkout")
async def checkout(dados: CheckoutSchema):
    if dados.metodo not in {"pix", "credito", "debito"}:
        raise HTTPException(status_code=400, detail="Método inválido")

    transacao_id = str(uuid.uuid4())
    prefer_real = bool(PAGSEGURO_TOKEN)

    if dados.metodo == "pix":
        try:
            result = _pagseguro_pix(dados, transacao_id)
            _pagamentos_memoria[result["transacao_id"]] = result["status"]
            return result
        except HTTPException:
            raise
        except Exception as e:
            _log_event("pagseguro_pix_erro", str(e))
            if prefer_real:
                raise HTTPException(status_code=502, detail="Pagamento PIX não processado.")
            raise

    # crédito ou débito
    try:
        result = _pagseguro_cartao(dados, transacao_id)
        _pagamentos_memoria[result["transacao_id"]] = result["status"]
        return result
    except HTTPException:
        raise
    except Exception as e:
        _log_event("pagseguro_cartao_erro", str(e))
        if prefer_real:
            raise HTTPException(status_code=502, detail="Pagamento cartão não processado.")
        raise


class WebhookPayload(BaseModel):
    id: str | None = None
    status: str | None = None
    event: str | None = None


@router.post("/webhook")
async def webhook(request: Request):
    """
    Endpoint para callbacks do Pagar.me com verificação opcional de assinatura HMAC (sha256).
    Header esperado: X-Hub-Signature ou X-Hub-Signature-256.
    """
    raw = await request.body()
    signature = request.headers.get("X-Hub-Signature") or request.headers.get("X-Hub-Signature-256")
    if not _verify_webhook(raw, signature):
        _log_event("webhook_rejeitado", f"signature={signature} body={raw[:500]!r}")
        raise HTTPException(status_code=401, detail="Assinatura inválida")

    payload = WebhookPayload.model_validate_json(raw)
    if payload.id:
        _pagamentos_memoria[payload.id] = payload.status or "desconhecido"
    _log_event("webhook_ok", f"id={payload.id} status={payload.status} event={payload.event}")
    return {"ok": True, "registrado": bool(payload.id)}


@router.get("/webhook/ping")
async def webhook_ping():
    """
    Endpoint simples para testar reachability do webhook no Render/Pagar.me.
    Não valida assinatura, apenas retorna ok.
    """
    return {"ok": True, "message": "webhook vivo"}


@router.get("/status/{transacao_id}")
async def status(transacao_id: str):
    """
    Consulta status de uma transação/charge no Pagar.me ou cache local.
    """
    pagarme_resp = _pagarme_status(transacao_id)
    if pagarme_resp:
        _pagamentos_memoria[transacao_id] = pagarme_resp["status"]
        return {"status": pagarme_resp["status"], "fonte": "pagarme"}
    if transacao_id in _pagamentos_memoria:
        return {"status": _pagamentos_memoria[transacao_id], "fonte": "cache"}
    raise HTTPException(status_code=404, detail="Transação não encontrada")
