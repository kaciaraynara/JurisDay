from fastapi import APIRouter
from datetime import datetime, timedelta

router = APIRouter()

@router.get("/listar")
def listar_prazos():
    hoje = datetime.now()
    
    # Simulação de dados vindos do Tribunal
    # No futuro, aqui entra a integração com API dos Tribunais
    return [
        {
            "processo": "0054321-88.2025.8.06.0001",
            "cliente": "Indústria Têxtil Ltda",
            "tipo": "Réplica à Contestação",
            "vencimento": (hoje + timedelta(days=2)).strftime("%d/%m/%Y"),
            "status": "URGENTE 🔴"
        },
        {
            "processo": "1029384-12.2025.8.06.0001",
            "cliente": "João das Couves",
            "tipo": "Audiência de Conciliação",
            "vencimento": (hoje + timedelta(days=15)).strftime("%d/%m/%Y"),
            "status": "No Prazo 🟢"
        }
    ]