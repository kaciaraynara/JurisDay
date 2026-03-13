"""
Smoke test para validar os fluxos web da API sem depender de serviços externos.
Executa: cadastro/login, /me, cadastro de cliente, checkout simulado, exportação DOCX/PDF.

Como rodar:
    python smoke.py
Certifique-se de estar na raiz do projeto e com as dependências instaladas.
"""

import uuid
from backend_api.main import app
from starlette.testclient import TestClient


def main():
    client = TestClient(app)
    email = f"adv_{uuid.uuid4().hex[:6]}@jurisday.com"
    cpf = uuid.uuid4().hex[:11]

    print("\n=== Cadastro advogado ===")
    r = client.post(
        "/auth/cadastrar",
        json={"nome_completo": "Dra Smoke", "cpf_cnpj": cpf, "email": email, "senha": "123456"},
    )
    print(r.status_code, r.json())

    print("\n=== Login ===")
    r = client.post("/auth/login", json={"email_ou_cnpj": email, "senha": "123456"})
    print(r.status_code, r.json())
    token = r.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    print("\n=== /auth/me ===")
    r = client.get("/auth/me", headers=headers)
    print(r.status_code, r.json())

    print("\n=== Cadastrar cliente ===")
    r = client.post(
        "/clientes/cadastrar",
        headers=headers,
        json={
            "nome": "Cliente Alpha",
            "cpf_cnpj": "00011122233",
            "email": "cliente@example.com",
            "whatsapp": "5511999999999",
            "numero_processo": "0000000-00.2024.8.26.0000",
            "tribunal": "TJSP",
        },
    )
    print(r.status_code, r.json())

    print("\n=== Checkout pix simulado ===")
    r = client.post("/planos/checkout", json={"plano": "essencial", "valor": 70, "metodo": "pix"})
    print(r.status_code, r.json())

    print("\n=== Exportar petição DOCX ===")
    r = client.post("/peticao/exportar", json={"texto": "Linha 1\nLinha 2", "formato": "docx"})
    print(r.status_code, r.headers.get("content-type"))

    print("\n=== Exportar petição PDF ===")
    r = client.post("/peticao/exportar", json={"texto": "Linha PDF", "formato": "pdf"})
    print(r.status_code, r.headers.get("content-type"))

    print("\nSmoke test concluído.")


if __name__ == "__main__":
    main()
