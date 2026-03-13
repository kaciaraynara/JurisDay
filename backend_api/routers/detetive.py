import os
from google import genai
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

# Chave lida do ambiente para evitar hardcode
MINHA_CHAVE_NOVA = os.getenv("GOOGLE_GENAI_KEY") or os.getenv("GENAI_KEY")

try:
    client = genai.Client(api_key=MINHA_CHAVE_NOVA) if MINHA_CHAVE_NOVA else None
    if client:
        print("✅ Motor da IA (detetive) ligado.")
except Exception as e:
    print(f"❌ Erro ao ligar a IA: {e}")
    client = None


class DetetiveSchema(BaseModel):
    nome_alvo: str
    cpf_cnpj: str


@router.post("/rastrear")
async def rastrear(dados: DetetiveSchema):
    try:
        if client is None:
            raise RuntimeError("Chave da Google AI ausente. Defina GOOGLE_GENAI_KEY no ambiente.")

        prompt = (
            "Atue como um consultor de inteligência financeira forense. "
            f"Alvo: {dados.nome_alvo}. Documento: {dados.cpf_cnpj}. "
            "Liste passos legais e bases públicas/privadas que o advogado pode consultar "
            "para localizar bens, contas, veículos e imóveis, sempre respeitando LGPD e devido processo. "
            "Entregue em tópicos práticos e priorizados."
        )
        response = client.models.generate_content(
            model="gemini-1.5-flash", contents=prompt
        )
        return {"estrategia": response.text}
    except Exception as e:
        print(f"❌ ERRO DETETIVE: {e}")
        raise HTTPException(status_code=500, detail=str(e))
