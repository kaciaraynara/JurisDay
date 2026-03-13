FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt
COPY . /app
# Fly usa 8080 por padrão; PORT vem de env (setado no fly.toml)
ENV PORT=8080
CMD ["sh", "-c", "uvicorn backend_api.main:app --host 0.0.0.0 --port ${PORT}"]
