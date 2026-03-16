import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import os
import sys
from pathlib import Path
from typing import List
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn
import time

# Import flexível: funciona tanto quando rodamos como pacote (backend_api.main)
# quanto quando executamos dentro da pasta backend_api (python main.py/uvicorn main:app).
try:
    from .routers import (
    auth,
    peticoes,
    dicionario,
    detetive,
    honorarios,
    suporte,
    monitoramento,
    pagamentos,
    clientes,
    prazos,
    calculadora,
    )
except ImportError:  # fallback para execução direta a partir da pasta backend_api
    here = Path(__file__).resolve().parent
    sys.path.append(str(here))            # permite "import routers"
    sys.path.append(str(here.parent))     # permite "import backend_api"
    from routers import (
        auth,
        peticoes,
        dicionario,
        detetive,
        honorarios,
        suporte,
        monitoramento,
        pagamentos,
        clientes,
        prazos,
        calculadora,
    )


def _cors_origins() -> List[str]:
    raw = os.getenv("ALLOWED_ORIGINS", "*")
    if raw.strip() == "*":
        return ["*"]
    return [o.strip() for o in raw.split(",") if o.strip()]


@asynccontextmanager
async def lifespan(app: FastAPI):
    monitoramento.ensure_scheduler_started()
    yield
    monitoramento.shutdown_scheduler()


app = FastAPI(
    title="JURISDAY PRO | API de Elite",
    description="Backend completo para automação jurídica, cálculos e monitoramento.",
    version="2.0.0",
    lifespan=lifespan,
)

# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Rate limit simples (login/cadastro): 5 req / 60s por IP ---
RATE_LIMIT_BUCKET = {}
RATE_LIMIT_MAX = 5
RATE_LIMIT_WINDOW = 60  # segundos


@app.middleware("http")
async def security_headers(request: Request, call_next):
    resp: Response

    # rate limit em login/cadastro
    path = request.url.path
    if path in {"/auth/login", "/auth/cadastrar"}:
        ip = request.client.host if request.client else "anon"
        now = time.time()
        bucket = RATE_LIMIT_BUCKET.get(ip, [])
        bucket = [t for t in bucket if now - t < RATE_LIMIT_WINDOW]
        if len(bucket) >= RATE_LIMIT_MAX:
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Muitas tentativas, aguarde.")
        bucket.append(now)
        RATE_LIMIT_BUCKET[ip] = bucket

    resp = await call_next(request)
    resp.headers.setdefault("X-Content-Type-Options", "nosniff")
    resp.headers.setdefault("X-Frame-Options", "DENY")
    resp.headers.setdefault("X-XSS-Protection", "1; mode=block")
    return resp


# --- Security Headers ---
# --- Routers ---
app.include_router(auth.router, prefix="/auth", tags=["Autenticação"])
app.include_router(peticoes.router, prefix="/peticao", tags=["Petições IA"])
app.include_router(dicionario.router, prefix="/dicionario", tags=["Dicionário"])
app.include_router(detetive.router, prefix="/detetive", tags=["Detetive de Bens"])
app.include_router(honorarios.router, prefix="/honorarios", tags=["Cálculos"])
app.include_router(suporte.router, prefix="/suporte", tags=["Suporte"])
app.include_router(monitoramento.router, prefix="/monitorar", tags=["Monitoramento JUS"])
app.include_router(pagamentos.router, prefix="/planos", tags=["Planos e Checkout"])
app.include_router(clientes.router, prefix="/clientes", tags=["Gestão de Clientes"])
app.include_router(prazos.router, prefix="/prazos", tags=["Prazos"])
app.include_router(calculadora.router, prefix="/calculadora", tags=["Calculadora"])


BASE_DIR = Path(__file__).resolve().parent.parent  # raiz do projeto
frontend_path = BASE_DIR / "frontend"
if frontend_path.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")


@app.get("/")
async def root():
    if frontend_path.exists():
        return FileResponse(frontend_path / "index.html")
    return {
        "status": "JurisDay Online",
        "mensagem": "Sistema operacional e seguro.",
        "documentacao": "/docs",
    }


@app.get("/app")
async def serve_app():
    if frontend_path.exists():
        return FileResponse(frontend_path / "index.html")
    return {"detail": "Não encontrado"}


if __name__ == "__main__":
    uvicorn.run("backend_api.main:app", host="0.0.0.0", port=8000, reload=True)
