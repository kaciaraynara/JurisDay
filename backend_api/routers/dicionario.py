import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from google import genai

router = APIRouter()

MINHA_CHAVE = os.getenv("GOOGLE_GENAI_KEY") or os.getenv("GENAI_KEY")

try:
    client = genai.Client(api_key=MINHA_CHAVE) if MINHA_CHAVE else None
except Exception as e:
    print(f"Erro de configuração: {e}")
    client = None

class DicionarioSchema(BaseModel):
    termo: str

@router.post("/consultar")
async def consultar(dados: DicionarioSchema):
    try:
        if client is None:
            raise RuntimeError("Chave da Google AI ausente. Defina GOOGLE_GENAI_KEY no ambiente.")
        # Mudamos para o modelo 1.5-flash que é o mais compatível de todos
        response = client.models.generate_content(
            model="gemini-1.5-flash", 
            contents=f"Explique juridicamente o termo: {dados.termo}"
        )
        return {"resposta": response.text}
    except Exception as e:
        print(f"❌ ERRO REAL NO TERMINAL: {e}")
        raise HTTPException(status_code=500, detail=str(e))
