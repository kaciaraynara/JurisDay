from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class DadosCalculo(BaseModel):
    complexidade: str # Baixa, Media, Alta
    horas_estimadas: int
    custo_fixo_escritorio: float

@router.post("/calcular")
def calcular_honorarios(dados: DadosCalculo):
    # Base de cálculo (exemplo de tabela base)
    valor_hora = 350.00  # Valor hora advogado júnior/pleno
    
    multiplicador = 1.0
    if dados.complexidade == "Media": multiplicador = 1.5
    if dados.complexidade == "Alta": multiplicador = 2.5

    custo_operacional = dados.custo_fixo_escritorio
    lucro_desejado = (dados.horas_estimadas * valor_hora * multiplicador)
    
    preco_final = custo_operacional + lucro_desejado
    
    return {
        "valor_sugerido": f"R$ {preco_final:,.2f}",
        "detalhes": f"Baseado em {dados.horas_estimadas}h de trabalho com complexidade {dados.complexidade}.",
        "msg_cliente": "Valor justo considerando a tecnicidade e tempo dedicado."
    }