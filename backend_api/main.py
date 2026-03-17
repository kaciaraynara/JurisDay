import sys
import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

# --- 1. CONFIGURAÇÃO DE CAMINHO (ESSENCIAL PARA O RENDER) ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.abspath(os.path.join(BASE_DIR, ".."))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)
if PROJECT_DIR not in sys.path:
    sys.path.append(PROJECT_DIR)

app = FastAPI(
    title="JURISDAY | Elite Inteligência Jurídica",
    description="Plataforma de Alta Performance para Advocacia Estratégica",
    version="1.0.0"
)

# --- 2. SEGURANÇA E ACESSO (CORS) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 3. SERVINDO O FRONTEND (CSS, JS, IMAGENS) ---
# Certifique-se de que a pasta 'frontend' está na raiz do projeto
FRONTEND_DIR = os.path.join(PROJECT_DIR, "frontend")
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

# --- 4. IMPORTAÇÃO DOS MÓDULOS (SÓ APÓS O SYS.PATH) ---
from routers import (
    auth,
    monitoramento,
    peticoes,
    dicionario,
    detetive,
    honorarios,
    pagamentos,
    clientes,
    prazos,
    calculadora,
    suporte,
)

app.include_router(auth.router, prefix="/auth", tags=["Autenticação"])
app.include_router(monitoramento.router, prefix="/monitorar", tags=["Monitoramento"])
app.include_router(peticoes.router, prefix="/peticao", tags=["Inteligência Artificial"])
app.include_router(dicionario.router, prefix="/dicionario", tags=["Dicionário"])
app.include_router(detetive.router, prefix="/detetive", tags=["Detetive"])
app.include_router(honorarios.router, prefix="/honorarios", tags=["Honorários"])
app.include_router(pagamentos.router, prefix="/planos", tags=["Planos e Checkout"])
app.include_router(clientes.router, prefix="/clientes", tags=["Clientes"])
app.include_router(prazos.router, prefix="/prazos", tags=["Prazos"])
app.include_router(calculadora.router, prefix="/calculadora", tags=["Calculadora"])
app.include_router(suporte.router, prefix="/suporte", tags=["Suporte"])

# --- 5. ROTAS DE NAVEGAÇÃO ---

@app.get("/")
async def serve_login():
    """Tela inicial deve ser login"""
    return FileResponse(os.path.join(FRONTEND_DIR, "login.html"))

@app.get("/app")
async def serve_app():
    return FileResponse(os.path.join(FRONTEND_DIR, "dashboard.html"))

@app.get("/login.html")
async def serve_login_html():
    return FileResponse(os.path.join(FRONTEND_DIR, "login.html"))

@app.get("/signup.html")
async def serve_signup_html():
    return FileResponse(os.path.join(FRONTEND_DIR, "signup.html"))

@app.get("/health")
async def health_check():
    """Verificação de integridade do sistema"""
    return {"status": "operacional", "sistema": "JURISDAY PRO"}
