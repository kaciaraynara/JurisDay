import os
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import jwt
from passlib.context import CryptContext
from pydantic import BaseModel

# Import compatível com execução como pacote ou dentro da pasta backend_api
try:
    from backend_api.db import obter_db
    import backend_api.models as models
except ImportError:
    from db import obter_db  # type: ignore
    import models as models  # type: ignore

router = APIRouter()

# Usamos pbkdf2_sha256 para evitar dependência de backends nativos do bcrypt em ambiente de testes.
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
oauth2_scheme = HTTPBearer(auto_error=False)

JWT_SECRET = os.getenv(
    "JWT_SECRET",
    "default-change-me-default-change-me-default-change-me-64chars"
)
JWT_ALG = os.getenv("JWT_ALG", "HS256")
JWT_EXPIRE_MIN = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))

class AdvogadoCreate(BaseModel):
    nome_completo: str
    cpf_cnpj: str
    oab: str | None = None
    email: str
    whatsapp: str | None = None
    senha: str
    plano: str = "Trial"
    logo_base64: str | None = None

class LoginSchema(BaseModel):
    email_ou_cnpj: str
    senha: str

class TokenOut(BaseModel):
    token: str
    nome: str
    expires_in: int


def _criar_token(sub: int) -> str:
    exp = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE_MIN)
    payload = {"sub": str(sub), "exp": exp}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)


def get_current_advogado(
    cred: HTTPAuthorizationCredentials = Depends(oauth2_scheme),
    db: Session = Depends(obter_db),
):
    if not cred:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token ausente")
    try:
        payload = jwt.decode(cred.credentials, JWT_SECRET, algorithms=[JWT_ALG])
        adv_id = payload.get("sub")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expirado")
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")

    adv = db.query(models.Advogado).filter(models.Advogado.id == int(adv_id)).first()
    if not adv:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuário não encontrado")
    return adv

@router.post("/cadastrar")
def cadastrar_advogado(advogado: AdvogadoCreate, db: Session = Depends(obter_db)):
    if db.query(models.Advogado).filter(models.Advogado.email == advogado.email).first():
        raise HTTPException(status_code=400, detail="E-mail já em uso.")
    if db.query(models.Advogado).filter(models.Advogado.cpf_cnpj == advogado.cpf_cnpj).first():
        raise HTTPException(status_code=400, detail="Documento já cadastrado.")

    senha_hash = pwd_context.hash(advogado.senha)
    novo = models.Advogado(
        nome_completo=advogado.nome_completo,
        cpf_cnpj=advogado.cpf_cnpj,
        oab=advogado.oab,
        email=advogado.email,
        whatsapp=advogado.whatsapp,
        senha_hash=senha_hash,
        plano_atual=advogado.plano,
        logo_base64=advogado.logo_base64,
    )
    db.add(novo)
    db.commit()
    db.refresh(novo)
    return {"mensagem": "Cadastro efetuado", "id": novo.id}


@router.post("/login", response_model=TokenOut)
def login(payload: LoginSchema, db: Session = Depends(obter_db)):
    adv = db.query(models.Advogado).filter(
        (models.Advogado.email == payload.email_ou_cnpj) | (models.Advogado.cpf_cnpj == payload.email_ou_cnpj)
    ).first()
    if not adv or not pwd_context.verify(payload.senha, adv.senha_hash):
        raise HTTPException(status_code=401, detail="Credenciais inválidas")
    token = _criar_token(adv.id)
    return TokenOut(token=token, nome=adv.nome_completo, expires_in=JWT_EXPIRE_MIN * 60)


@router.get("/me")
def me(usuario=Depends(get_current_advogado)):
    return {
        "id": usuario.id,
        "nome": usuario.nome_completo,
        "email": usuario.email,
        "plano": usuario.plano_atual,
        "whatsapp": usuario.whatsapp,
    }
