import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import google.generativeai as genai
from io import BytesIO
from fastapi.responses import StreamingResponse
from docx import Document
from fpdf import FPDF

router = APIRouter()

# Preferimos ler a chave de ambiente para não vazar no código
CHAVE_API = os.getenv("GOOGLE_GENAI_KEY") or os.getenv("GENAI_KEY")

try:
    client = genai.Client(api_key=CHAVE_API) if CHAVE_API else None
except Exception as e:
    print(f"⚠️ Erro ao iniciar cliente Gemini: {e}")
    client = None

class PeticaoSchema(BaseModel):
    cliente_nome: str
    reu_nome: str
    tipo_acao: str
    fatos_relatados: str
    juizo_destino: str | None = None


class ExportSchema(BaseModel):
    texto: str
    formato: str  # docx ou pdf

@router.post("/gerar")
async def gerar_peticao(dados: PeticaoSchema):
    try:
        if client is None:
            raise RuntimeError("Chave da Google AI ausente. Defina GOOGLE_GENAI_KEY no ambiente.")
        prompt = (
            "Elabore uma petição inicial completa, com endereçamento correto ao juízo informado, "
            "qualificação das partes, narrativa fática organizada, fundamentos jurídicos "
            "(doutrina + jurisprudência recente do STJ/STF quando aplicável), pedidos claros, "
            "valor da causa e requerimentos finais. "
            f"Juízo: {dados.juizo_destino or 'definir juízo adequado'}. "
            f"Tipo de ação: {dados.tipo_acao}. "
            f"Autor: {dados.cliente_nome}. Réu: {dados.reu_nome}. "
            f"Fatos essenciais: {dados.fatos_relatados}. "
            "Mantenha linguagem forense profissional e estrutura com títulos."
        )
        response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
        return {"peticao_texto": response.text}
    except Exception as e:
        print(f"❌ ERRO NA IA: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _gerar_docx(texto: str) -> BytesIO:
    doc = Document()
    for linha in texto.split("\n"):
        doc.add_paragraph(linha)
    buf = BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf


def _gerar_pdf(texto: str) -> BytesIO:
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    for linha in texto.split("\n"):
        pdf.multi_cell(0, 10, text=linha)
    raw = pdf.output()  # retorna bytes no fpdf2
    pdf_bytes = raw if isinstance(raw, (bytes, bytearray)) else raw.encode("latin-1")
    return BytesIO(pdf_bytes)


@router.post("/exportar")
async def exportar_peticao(payload: ExportSchema):
    try:
        texto = payload.texto or ""
        formato = payload.formato.lower()
        if formato == "doc" or formato == "docx":
            buf = _gerar_docx(texto)
            filename = "peticao-jurisday.docx"
            media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        elif formato == "pdf":
            buf = _gerar_pdf(texto)
            filename = "peticao-jurisday.pdf"
            media_type = "application/pdf"
        else:
            raise HTTPException(status_code=400, detail="Formato não suportado")

        return StreamingResponse(buf, media_type=media_type, headers={"Content-Disposition": f"attachment; filename={filename}"})
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ ERRO EXPORTAR: {e}")
        raise HTTPException(status_code=500, detail=str(e))
