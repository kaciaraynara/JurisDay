import sys
import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

# --- 1. CONFIGURAÇÃO DE CAMINHO (ESSENCIAL PARA O RENDER) ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

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
app.mount("/static", StaticFiles(directory="frontend"), name="static")

# --- 4. IMPORTAÇÃO DOS MÓDULOS (SÓ APÓS O SYS.PATH) ---
from routers import auth, monitoramento, peticoes

app.include_router(auth.router, prefix="/auth", tags=["Autenticação"])
app.include_router(monitoramento.router, prefix="/monitorar", tags=["Monitoramento"])
app.include_router(peticoes.router, prefix="/peticao", tags=["Inteligência Artificial"])

# --- 5. ROTAS DE NAVEGAÇÃO ---

@app.get("/")
async def serve_index():
    """Entrega o Dashboard Principal do JURISDAY"""
    return FileResponse('frontend/index.html')

@app.get("/health")
async def health_check():
    """Verificação de integridade do sistema"""
    return {"status": "operacional", "sistema": "JURISDAY PRO"}