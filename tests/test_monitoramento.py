import os
os.environ["DATABASE_URL"] = "sqlite:///./test_monitor.db"

from fastapi.testclient import TestClient
import backend_api.main as main
import backend_api.routers.monitoramento as mon

client = TestClient(main.app)

def _auth_headers():
    client.post('/auth/cadastrar', json={
        "nome_completo": "Teste", "cpf_cnpj": "123", "email": "teste@x.com", "senha": "123", "whatsapp": "5511999999999"
    })
    r = client.post('/auth/login', json={"email_ou_cnpj": "teste@x.com", "senha": "123"})
    token = r.json()["token"]
    return {"Authorization": f"Bearer {token}"}


def test_monitoramento_registrar_listar(monkeypatch):
    # garante tabela limpa
    mon.models.Base.metadata.drop_all(bind=mon.engine)
    mon.models.Base.metadata.create_all(bind=mon.engine)
    headers = _auth_headers()

    def fake_get(url, headers=None, timeout=10, params=None):
        class R:
            status_code = 200
            def json(self):
                return {"status":"andamento","andamento":"citado"}
        return R()
    monkeypatch.setattr(mon.requests, "get", fake_get)

    r = client.post('/monitorar/registrar', json={
        "numero": "000", "tribunal": "TJSP", "parte": "Autor", "telefone_cliente": "5511999999999"
    }, headers=headers)
    assert r.status_code == 200

    r2 = client.post('/monitorar/rodar', headers=headers)
    assert r2.status_code == 200
    data = r2.json()
    assert data['processos'][0]['status'] == 'andamento'

    def fake_post(url, json=None, timeout=10):
        class R:
            status_code = 200
        return R()
    monkeypatch.setattr(mon.requests, "post", fake_post)

    r3 = client.post('/monitorar/resumo', headers=headers)
    assert r3.status_code == 200
    payload = r3.json()
    assert 'Resumo diário' in payload['mensagem']
    assert payload['envios'][0]['enviado'] in (True, False)

    r4 = client.get('/monitorar/status', headers=headers)
    assert r4.status_code == 200
