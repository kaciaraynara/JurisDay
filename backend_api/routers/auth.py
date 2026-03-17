import os
import re
import jwt
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr

from db import obter_db
import models

router = APIRouter()
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
oauth2_scheme = HTTPBearer(auto_error=False)

JWT_SECRET = os.getenv("JWT_SECRET", "jurisday-enterprise-edition-2026")
JWT_ALG = "HS256"
JWT_EXPIRE_MIN = 120

class AdvogadoCreate(BaseModel):
    nome_completo: str
    cpf_cnpj: str
    oab: str | None = None
    email: EmailStr
    whatsapp: str | None = None
    senha: str
    lembrete_senha: str | None = None
    plano: str = "Trial"
    logo_base64: str | None = None

    def validar_senha(self):
        """Regras de Senha Forte para Grandes Escritórios"""
        if len(self.senha) < 8:
            return "A senha deve ter no mínimo 8 caracteres."
        if not re.search(r"[A-Z]", self.senha):
            return "A senha deve conter ao menos uma letra maiúscula."
        if not re.search(r"[0-9]", self.senha):
            return "A senha deve conter ao menos um número."
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", self.senha):
            return "A senha deve conter ao menos um caractere especial."
        return None

@router.post("/cadastrar", status_code=status.HTTP_201_CREATED)
def cadastrar(advogado: AdvogadoCreate, db: Session = Depends(obter_db)):
    erro_senha = advogado.validar_senha()
    if erro_senha:
        raise HTTPException(status_code=400, detail=erro_senha)

    if db.query(models.Advogado).filter(models.Advogado.email == advogado.email).first():
        raise HTTPException(status_code=400, detail="Este e-mail já está em uso.")
    
    if db.query(models.Advogado).filter(models.Advogado.cpf_cnpj == advogado.cpf_cnpj).first():
        raise HTTPException(status_code=400, detail="Este CPF/CNPJ já está cadastrado.")

    senha_hash = pwd_context.hash(advogado.senha)
    novo = models.Advogado(
        nome_completo=advogado.nome_completo,
        cpf_cnpj=advogado.cpf_cnpj,
        oab=advogado.oab,
        email=advogado.email,
        whatsapp=advogado.whatsapp,
        senha_hash=senha_hash,
        lembrete_senha=advogado.lembrete_senha,
        logo_base64=advogado.logo_base64
    )
    db.add(novo)
    db.commit()
    db.refresh(novo)
    return {"status": "sucesso", "mensagem": "Perfil jurídico criado com segurança."}

@router.post("/login")
def login(payload: dict, db: Session = Depends(obter_db)):
    # Permite login por e-mail ou CPF/CNPJ
    identificador = payload.get("email_ou_cnpj")
    user = db.query(models.Advogado).filter(
        (models.Advogado.email == identificador) | (models.Advogado.cpf_cnpj == identificador)
    ).first()
    
    if not user or not pwd_context.verify(payload.get("senha"), user.senha_hash):
        raise HTTPException(status_code=401, detail="Credenciais inválidas.")
    
    exp = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE_MIN)
    token = jwt.encode({"sub": str(user.id), "exp": exp}, JWT_SECRET, algorithm=JWT_ALG)
    return {"token": token, "nome": user.nome_completo, "expires_in": JWT_EXPIRE_MIN * 60}