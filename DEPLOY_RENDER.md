# Deploy no Render (Docker + Postgres)

1) Requisitos no repositório (já presentes):
   - `Dockerfile` (usa uvicorn e respeita PORT do Render)
   - `render.yaml` (provisiona Postgres starter e serviço web docker)
   - `requirements.txt`

2) Variáveis de ambiente no painel do Render (Settings > Environment):
   - `GOOGLE_GENAI_KEY`
   - `JWT_SECRET` (64+ chars)
   - `PAGARME_API_KEY` (se usar cobrança real)
   - `MAIL_HOST`, `MAIL_PORT`, `MAIL_USER`, `MAIL_PASS`, `MAIL_FROM`, `MAIL_TO`
   - `ALLOWED_ORIGINS` (domínio público, já sugerido: https://jurisday.onrender.com)
   - O Render injeta `DATABASE_URL` automaticamente a partir do Postgres criado no `render.yaml`.

3) Fluxo de deploy:
   - Conecte o repo ao Render e habilite “Blueprint (render.yaml)”.
   - Escolha região próxima (já definido `oregon`; ajuste se quiser).
   - Primeiro deploy: o serviço web sobe com `uvicorn backend_api.main:app --host 0.0.0.0 --port $PORT`.
   - Health check em `/docs` (já configurado em `render.yaml`).

4) Frontend:
   - Servido pelo próprio backend:
     - `/static/login.html`
     - `/static/signup.html`
     - `/app` (dashboard)

5) Dicas:
   - Se trocar domínio, ajuste `ALLOWED_ORIGINS` no painel.
   - Para logs: Render > Service > Logs.
   - Para migrações futuras: incluir ferramenta (alembic) ou script custom e chamar no startCommand.
