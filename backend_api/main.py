# No topo, junto com os outros imports de routers:
from routers import auth, peticoes # Adicione o 'peticoes' aqui

# Embaixo, onde você incluiu o router de auth:
app.include_router(peticoes.router, prefix="/peticao", tags=["Inteligência Artificial"])
import sys
import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

# Injeção de Path para reconhecimento de módulos no ambiente Linux/Render
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

app = FastAPI(
    title="JURISDAY | Elite Inteligência Jurídica",
    description="Plataforma de Alta Performance para Advocacia Estratégica",
    version="1.0.0"
)

# Configuração de CORS para segurança de dados
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Servindo Arquivos Estáticos (CSS, JS, Imagens)
# Certifique-se que a pasta se chama 'frontend' na raiz do projeto
app.mount("/static", StaticFiles(directory="frontend"), name="static")

# Importação de Roteadores (Ajuste conforme seus arquivos existentes)
from routers import auth, monitoramento, peticoes

app.include_router(auth.router, prefix="/auth", tags=["Autenticação"])
app.include_router(monitoramento.router, prefix="/monitorar", tags=["Monitoramento"])
app.include_router(peticoes.router, prefix="/peticao", tags=["Inteligência Artificial"])

@app.get("/")
async def serve_index():
    """Entrega o Dashboard Principal"""
    return FileResponse('frontend/index.html')

@app.get("/health")
async def health_check():
    return {"status": "operacional", "sistema": "JURISDAY PRO"}