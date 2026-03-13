import types
from fastapi.testclient import TestClient

from backend_api.main import app
import backend_api.routers.peticoes as peticoes
import backend_api.routers.dicionario as dicionario
import backend_api.routers.detetive as detetive


class _FakeModel:
    def generate_content(self, model=None, contents=None):
        return types.SimpleNamespace(text="texto-falso")


class _FakeClient:
    def __init__(self):
        self.models = _FakeModel()


# Fixtures via monkeypatch inside tests because pytest not imported here

def _patch_clients():
    peticoes.client = _FakeClient()
    dicionario.client = _FakeClient()
    detetive.client = _FakeClient()


client = TestClient(app)


def test_peticao_gerar():
    _patch_clients()
    resp = client.post("/peticao/gerar", json={
        "cliente_nome": "A", "reu_nome": "B", "tipo_acao": "C", "fatos_relatados": "Fatos"
    })
    assert resp.status_code == 200
    assert "peticao_texto" in resp.json()


def test_dicionario_consultar():
    _patch_clients()
    resp = client.post("/dicionario/consultar", json={"termo": "jurisprudencia"})
    assert resp.status_code == 200
    assert resp.json()["resposta"] == "texto-falso"


def test_detetive_rastrear():
    _patch_clients()
    resp = client.post("/detetive/rastrear", json={"nome_alvo": "X", "cpf_cnpj": "000"})
    assert resp.status_code == 200
    assert "estrategia" in resp.json()


def test_exportar_docx():
    _patch_clients()
    resp = client.post("/peticao/exportar", json={"texto": "linha 1\nlinha 2", "formato": "doc"})
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("application/vnd.openxmlformats-officedocument.wordprocessingml.document")


def test_exportar_pdf():
    _patch_clients()
    resp = client.post("/peticao/exportar", json={"texto": "linha", "formato": "pdf"})
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("application/pdf")


def test_exportar_formato_invalido():
    resp = client.post("/peticao/exportar", json={"texto": "x", "formato": "txt"})
    assert resp.status_code == 400
