import os
import uuid
import hmac
import hashlib
from datetime import datetime, timedelta, timezone
import requests
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

router = APIRouter()

PAGARME_API_KEY = os.getenv("PAGARME_API_KEY")
PAGARME_BASE_URL = os.getenv("PAGARME_BASE_URL", "https://api.pagar.me/core/v5")
PAGARME_WEBHOOK_SECRET = os.getenv("PAGARME_WEBHOOK_SECRET")
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
    validade: str | None = None
    cvv: str | None = None


def _simular_pix(valor: float, transacao_id: str):
    # chave PIX fixa solicitada: 88997620407 (pode ser telefone/código de cobrança)
    chave_pix = "88997620407"
    codigo_pix = (
        f"00020126580014BR.GOV.BCB.PIX01{len(chave_pix):02d}{chave_pix}"
        f"520400005303986540{int(valor*100):010d}5802BR5920JURISDAY INTELIGENCIA"
        f"6009SAO PAULO62290525{transacao_id[:25]}6304"
    )
    return {
        "status": "pendente",
        "transacao_id": transacao_id,
        "metodo": "pix",
        "codigo_pix": codigo_pix,
        "mensagem": "Use o copia e cola para pagar por PIX. Liberação em segundos após confirmação.",
        "trial": True,
        "trial_dias": TRIAL_DIAS,
        "cobrar_em": (datetime.now(timezone.utc) + timedelta(days=TRIAL_DIAS)).date().isoformat(),
    }


def _simular_cartao(dados: CheckoutSchema, transacao_id: str):
    if not (dados.nome_titular and dados.numero_cartao and dados.validade and dados.cvv):
        raise HTTPException(status_code=400, detail="Dados do cartão incompletos")
    cartao_mascarado = f"**** **** **** {dados.numero_cartao[-4:]}"
    return {
        "status": "aprovado",
        "transacao_id": transacao_id,
        "metodo": dados.metodo,
        "cartao": cartao_mascarado,
        "mensagem": "Pagamento confirmado. Plano liberado imediatamente.",
        "trial": True,
        "trial_dias": TRIAL_DIAS,
        "cobrar_em": (datetime.now(timezone.utc) + timedelta(days=TRIAL_DIAS)).date().isoformat(),
    }


def _pagarme_payload(dados: CheckoutSchema):
    return {
        "items": [{"amount": int(dados.valor * 100), "description": f"Plano {dados.plano}", "quantity": 1}],
        "payments": [
            {
                "payment_method": "pix" if dados.metodo == "pix" else "credit_card",
                "pix": {"expires_in": 3600} if dados.metodo == "pix" else None,
                "credit_card": {
                    "installments": 1,
                    "card": {
                        "holder_name": dados.nome_titular,
                        "number": dados.numero_cartao,
                        "exp_month": dados.validade.split("/")[0] if dados.validade else None,
                        "exp_year": f"20{dados.validade.split('/')[1]}" if dados.validade else None,
                        "cvv": dados.cvv,
                    },
                }
                if dados.metodo in {"credito", "debito"}
                else None,
            }
        ],
        "customer": {"name": dados.nome_titular or "Cliente JurisDay"},
    }


def _pagarme_checkout(dados: CheckoutSchema):
    if not PAGARME_API_KEY:
        return None  # indica fallback para simulação
    headers = {"Authorization": f"Basic {PAGARME_API_KEY}"}
    try:
        resp = requests.post(f"{PAGARME_BASE_URL}/orders", json=_pagarme_payload(dados), headers=headers, timeout=15)
        if resp.status_code >= 400:
            raise HTTPException(status_code=resp.status_code, detail=resp.text)
        data = resp.json()
        pay = data["charges"][0]["last_transaction"]
        if dados.metodo == "pix":
            return {
                "status": pay.get("status", "pendente"),
                "transacao_id": pay.get("id"),
                "metodo": "pix",
                "codigo_pix": pay.get("qr_code", {}).get("text") or pay.get("qr_code") or "",
                "mensagem": "Use o código PIX para pagar. Liberação automática após confirmação.",
                "trial": True,
                "trial_dias": TRIAL_DIAS,
                "cobrar_em": (datetime.now(timezone.utc) + timedelta(days=TRIAL_DIAS)).date().isoformat(),
            }
        else:
            return {
                "status": pay.get("status", "aprovado"),
                "transacao_id": pay.get("id"),
                "metodo": dados.metodo,
                "cartao": pay.get("card", {}).get("last_four") and f"**** **** **** {pay['card']['last_four']}",
                "mensagem": "Pagamento confirmado. Plano liberado imediatamente.",
                "trial": True,
                "trial_dias": TRIAL_DIAS,
                "cobrar_em": (datetime.now(timezone.utc) + timedelta(days=TRIAL_DIAS)).date().isoformat(),
            }
    except HTTPException:
        raise
    except Exception as e:
        # fallback para simulação em caso de erro na integração
        print(f"⚠️ Erro pagar.me, usando simulação: {e}")
        return None


def _pagseguro_checkout(dados: CheckoutSchema):
    """
    Integração básica PagSeguro: suporta PIX real se PAGSEGURO_TOKEN estiver definido.
    Cartão permanece em simulação para evitar tokenização client-side neste MVP.
    """
    if not PAGSEGURO_TOKEN:
        return None
    if dados.metodo != "pix":
        return None  # só PIX no fluxo PagSeguro por enquanto

    headers = {
        "Authorization": f"Bearer {PAGSEGURO_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    ref_id = str(uuid.uuid4())[:18]
    payload = {
        "reference_id": ref_id,
        "description": f"Plano {dados.plano}",
        "amount": {"value": int(dados.valor * 100), "currency": "BRL"},
        "payment_method": {"type": "PIX"},
        "notification_urls": [],  # pode adicionar webhook se desejar
    }
    try:
        resp = requests.post(f"{PAGSEGURO_BASE_URL}/charges", json=payload, headers=headers, timeout=20)
        if resp.status_code >= 400:
            raise HTTPException(status_code=resp.status_code, detail=resp.text)
        data = resp.json()
        qr = ""
        try:
            qr = data.get("payment_response", {}).get("qr_codes", [{}])[0].get("text", "")
        except Exception:
            qr = ""
        return {
            "status": data.get("status", "pending"),
            "transacao_id": data.get("id", ref_id),
            "metodo": "pix",
            "codigo_pix": qr,
            "mensagem": "Use o copia e cola para pagar por PIX (PagSeguro).",
            "trial": True,
            "trial_dias": TRIAL_DIAS,
            "cobrar_em": (datetime.now(timezone.utc) + timedelta(days=TRIAL_DIAS)).date().isoformat(),
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"⚠️ Erro PagSeguro, caindo para simulação: {e}")
        return None


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
    prefer_real = bool(PAGARME_API_KEY or PAGSEGURO_TOKEN)

    # tenta pagar.me se chave presente
    pagarme_result = _pagarme_checkout(dados)
    if pagarme_result:
        _pagamentos_memoria[pagarme_result["transacao_id"]] = pagarme_result["status"]
        return pagarme_result

    # tenta PagSeguro (PIX) se chave presente
    pagseguro_result = _pagseguro_checkout(dados)
    if pagseguro_result:
        _pagamentos_memoria[pagseguro_result["transacao_id"]] = pagseguro_result["status"]
        return pagseguro_result

    # se há provedores configurados mas falhou, não simular
    if prefer_real:
        if dados.metodo != "pix":
            raise HTTPException(status_code=400, detail="Cartão não habilitado ainda. Use PIX.")
        raise HTTPException(status_code=502, detail="Pagamento não processado. Tente novamente.")

    # fallback simulado (modo demo)
    if dados.metodo == "pix":
        result = _simular_pix(dados.valor, transacao_id)
    else:
        result = _simular_cartao(dados, transacao_id)
    _pagamentos_memoria[result["transacao_id"]] = result["status"]
    return result


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
