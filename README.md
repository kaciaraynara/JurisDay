# JURISDAY – IA jurídica pronta para validar clientes

Stack: FastAPI + JWT, Pagar.me (cartão/PIX), FPDF2, APScheduler, frontend estático (PWA light) servido pelo próprio backend.

## Visão rápida
- Autenticação JWT (email/CPF/CNPJ + senha). Cadastro aceita logo; OAB é opcional. Trial padrão: 7 dias.
- Petições com IA: gera PDF timbrado, download direto pelo front.
- Monitoramento JUS: tarefas agendadas, resumo e webhook para WhatsApp.
- Pagamentos: integra Pagar.me se a chave existir; fallback simulado com PIX (chave 88997620407) e cartão. Retorna `trial_dias` e `cobrar_em`.
- Suporte: POST `/suporte` envia e-mail (SMTP) ou registra em `backend_api/data/suporte.log`.
- PWA: `manifest.json`, `sw.js`, botão “Instalar” e botão “Fale conosco”.

## Estrutura de pastas
- `backend_api/main.py` – app FastAPI, CORS, security headers, rate limit de login/cadastro.
- `backend_api/routers/` – `auth`, `peticoes`, `monitoramento`, `pagamentos`, `suporte`, etc.
- `frontend/` – `index.html` (landing/dashboard), `login.html`, `signup.html`, `style.css`, `manifest.json`, `icon.svg`, `sw.js`.
- `smoke.py` – fluxo rápido fim‑a‑fim (login → IA → checkout → export).

## Variáveis de ambiente (copie de `.env.example`)
- Banco: `DATABASE_URL` (se vazio usa SQLite local).
- IA: `GOOGLE_GENAI_KEY`.
- JUS/WhatsApp: `JUS_API_URL`, `JUS_API_TOKEN`, `WHATSAPP_WEBHOOK_URL`.
- Pagamentos: `PAGARME_API_KEY`, `PAGARME_BASE_URL`, `PAGARME_WEBHOOK_SECRET` (assinar webhooks).
- Auth: `JWT_SECRET` (>=32 chars), `JWT_EXPIRE_MINUTES`.
- Monitoramento: `MONITOR_INTERVAL_MINUTES`, `MONITOR_DB_PATH`.
- Trial: `TRIAL_DIAS` (padrão 7).
- SMTP suporte: `MAIL_HOST`, `MAIL_PORT`, `MAIL_USER`, `MAIL_PASS`, `MAIL_FROM`, `MAIL_TO`.
- CORS: `ALLOWED_ORIGINS`.

## Rodando localmente (Windows/Unix)
```bash
# na raiz do projeto
python -m uvicorn backend_api.main:app --reload --port 8000
# se a porta 8000 estiver ocupada, altere --port 8001/8002
```
Front servido pelo backend:
- Landing/dashboard: http://127.0.0.1:8000/app
- Login: http://127.0.0.1:8000/static/login.html
- Cadastro: http://127.0.0.1:8000/static/signup.html

## Testes
```bash
python -m pytest tests/test_api.py tests/test_monitoramento.py tests/test_pagamentos.py
```
Se estiver no OneDrive e aparecer `PermissionError` em pastas `tests/pytest-cache-files-*`, apague-as ou mova o projeto para fora do OneDrive e rode novamente.

## Deploy rápido (Render ou similar)
- Usar `Dockerfile` da raiz.
- Configurar todas as envs acima (em produção prefira Postgres em vez de SQLite).
- Ajustar `ALLOWED_ORIGINS` para o domínio público.
- Front já é servido por `/static` e `/app`, não precisa Vercel separado.

## Dicas de operação
- Para iniciar a partir da pasta `backend_api`, use `python -m uvicorn main:app --reload`.
- Erro `ModuleNotFoundError: backend_api`: significa que o comando não foi rodado na raiz ou o módulo foi chamado com prefixo duplicado.
- Erro `WinError 10048`: a porta está em uso; troque a porta ou finalize o processo antigo.
- Banco SQLite: garanta que o diretório de destino existe e tem permissão de escrita.

## Segurança aplicada
- Rate limit 5 req/60s em login/cadastro.
- Headers: `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `X-XSS-Protection: 1; mode=block`.
- JWT com expiração configurável.
- `.env` já ignorado no `.gitignore`; não commitar segredos.

## Suporte e feedback
- Contato padrão: jurisdaycontato@gmail.com via endpoint `/suporte`.
- Front possui botão “Fale conosco” e “Instalar App” (PWA) para engajamento.
