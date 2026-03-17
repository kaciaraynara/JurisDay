import os
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
import stripe

router = APIRouter()

STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
STRIPE_SUCCESS_URL = os.getenv("STRIPE_SUCCESS_URL", "https://example.com/sucesso")
STRIPE_CANCEL_URL = os.getenv("STRIPE_CANCEL_URL", "https://example.com/cancelado")

PLANO_NOME = "Plano Profissional"
PLANO_VALOR_CENTS = 4999  # R$ 49,99
PLANO_MOEDA = "brl"

if STRIPE_SECRET_KEY:
    stripe.api_key = STRIPE_SECRET_KEY


class CheckoutSchema(BaseModel):
    email: str | None = None
    nome: str | None = None


@router.post("/checkout")
async def criar_checkout(payload: CheckoutSchema):
    if not STRIPE_SECRET_KEY:
        raise HTTPException(status_code=500, detail="Stripe não configurado")
    try:
        session = stripe.checkout.Session.create(
            mode="subscription",
            customer_email=payload.email,
            line_items=[
                {
                    "price_data": {
                        "currency": PLANO_MOEDA,
                        "product_data": {"name": PLANO_NOME},
                        "recurring": {"interval": "month"},
                        "unit_amount": PLANO_VALOR_CENTS,
                    },
                    "quantity": 1,
                }
            ],
            success_url=STRIPE_SUCCESS_URL + "?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=STRIPE_CANCEL_URL,
        )
        return {"checkout_url": session.url, "session_id": session.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webhook")
async def stripe_webhook(request: Request):
    if not STRIPE_WEBHOOK_SECRET:
        return {"ok": True, "warning": "Webhook secret não configurado"}
    payload = await request.body()
    sig = request.headers.get("stripe-signature")
    try:
        event = stripe.Webhook.construct_event(payload, sig, STRIPE_WEBHOOK_SECRET)
    except Exception:
        raise HTTPException(status_code=400, detail="Assinatura inválida")

    # Aqui você pode atualizar status no banco conforme evento
    if event["type"] in {"checkout.session.completed", "invoice.paid"}:
        pass
    return {"ok": True}

