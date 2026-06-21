import asyncio
import random


# Simula o pagamento
async def solicitar_pagamento_mock(valor: float, pedido_id: int):
    # Finge demora da rede
    await asyncio.sleep(1.5)

# Se o valor for exatamente 999, simula erro, caso contrário aprova.
    if valor == 999.0:
        return {
            "sucesso": False,
            "status": "NEGADO",
            "motivo": "Saldo insuficiente ou cartão bloqueado"
        }

    return {
        "sucesso": True,
        "status": "APROVADO",
        "transacao_id": f"TX-{pedido_id}-998877"
    }
