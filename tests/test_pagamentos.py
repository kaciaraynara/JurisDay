from fastapi.testclient import TestClient
import backend_api.main as main

client = TestClient(main.app)


def test_pagamento_pix():
    r = client.post('/planos/checkout', json={
        "plano": "essencial", "valor": 70, "metodo": "pix"
    })
    assert r.status_code == 200
    data = r.json()
    assert data['metodo'] == 'pix'
    assert 'codigo_pix' in data


def test_pagamento_cartao_incompleto():
    r = client.post('/planos/checkout', json={
        "plano": "pro", "valor": 150, "metodo": "credito"
    })
    assert r.status_code == 400


def test_pagamento_cartao_ok():
    r = client.post('/planos/checkout', json={
        "plano": "pro", "valor": 150, "metodo": "debito",
        "nome_titular": "Teste", "numero_cartao": "4111111111111111", "validade": "12/30", "cvv": "123"
    })
    assert r.status_code == 200
    data = r.json()
    assert data['status'] == 'aprovado'
    assert data['cartao'].endswith('1111')
