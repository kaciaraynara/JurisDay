import os
import smtplib
from email.message import EmailMessage
from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr

router = APIRouter()


class SuporteMensagem(BaseModel):
    nome: str
    email: EmailStr
    mensagem: str


def _send_email(msg: SuporteMensagem) -> bool:
    """
    Envia e-mail via SMTP se variáveis estiverem configuradas.
    Retorna True se enviado, False se caiu em fallback.
    """
    host = os.getenv("MAIL_HOST")
    user = os.getenv("MAIL_USER")
    password = os.getenv("MAIL_PASS")
    port = int(os.getenv("MAIL_PORT", "587"))
    to_addr = os.getenv("MAIL_TO", "jurisdaycontato@gmail.com")
    from_addr = os.getenv("MAIL_FROM", user or to_addr)

    if not (host and user and password):
        return False

    email = EmailMessage()
    email["Subject"] = f"[JurisDay Suporte] {msg.nome}"
    email["From"] = from_addr
    email["To"] = to_addr
    corpo = f"Nome: {msg.nome}\nEmail: {msg.email}\n\nMensagem:\n{msg.mensagem}"
    email.set_content(corpo)

    try:
        with smtplib.SMTP(host, port, timeout=10) as s:
            s.starttls()
            s.login(user, password)
            s.send_message(email)
        return True
    except Exception:
        return False


def _fallback_log(msg: SuporteMensagem):
    data_dir = Path(__file__).resolve().parent.parent / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    log_file = data_dir / "suporte.log"
    with log_file.open("a", encoding="utf-8") as f:
        f.write(f"{msg.nome} <{msg.email}>: {msg.mensagem}\n---\n")


@router.post("/suporte")
async def suporte(msg: SuporteMensagem):
    if not msg.mensagem.strip():
        raise HTTPException(status_code=400, detail="Mensagem vazia")
    enviado = _send_email(msg)
    if not enviado:
        _fallback_log(msg)
    return {"ok": True, "enviado_email": enviado}
