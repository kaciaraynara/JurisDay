# Deploy rápido
1. Copie `.env.example` para `.env` e preencha as chaves (GENAI, JUS, PAGARME, WHATSAPP, DATABASE_URL).
2. Suba com Docker: `docker-compose up -d` (API em http://localhost:8000, Postgres interno).
3. Acesse http://localhost:8000 para o front; FastAPI serve o index.
4. Para produção, use um reverse proxy (nginx) e rode múltiplos workers: `uvicorn backend_api.main:app --host 0.0.0.0 --port 8000 --workers 4` ou gunicorn.

# Observações
- Banco: Postgres recomendado (já configurado no compose). Ajuste `DATABASE_URL` se usar RDS/CloudSQL.
- Integrações: Pagar.me real (PAGARME_API_KEY), IA (GOOGLE_GENAI_KEY), JUS (JUS_API_URL/JUS_API_TOKEN), WhatsApp webhook.
- CORS: configure ALLOWED_ORIGINS para o domínio do front.
- Tarefas agendadas: APScheduler roda no mesmo contêiner; para alta carga considere mover para um worker dedicado ou Celery.
- Testes: `pytest` após `pip install -r requirements.txt`.
