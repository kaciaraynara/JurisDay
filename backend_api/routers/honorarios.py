from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class DadosCalculo(BaseModel):
    horas_estimadas: int
    complexidade: str
    custo_fixo_escritorio: float

@router.post("/calcular")
def calcular_honorarios(dados: DadosCalculo):
    # Valor base da hora de trabalho de um advogado (referência inicial)
    valor_hora_base = 250.00
    
    # Multiplicador de acordo com a dificuldade da causa
    multiplicador = 1.0
    if dados.complexidade == "Media":
        multiplicador = 1.5
    elif dados.complexidade == "Alta":
        multiplicador = 2.0
        
    # Cálculo matemático
    valor_servico = (dados.horas_estimadas * valor_hora_base) * multiplicador
    valor_final = valor_servico + dados.custo_fixo_escritorio
    
    # Formatação profissional para a tela
    valor_formatado = f"R$ {valor_final:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    
    detalhes = f"Cálculo baseado em {dados.horas_estimadas}h de trabalho técnico em causa de complexidade {dados.complexidade}, acrescido do custo operacional do escritório."
    
    return {
        "valor_sugerido": valor_formatado,
        "detalhes": detalhes
    }