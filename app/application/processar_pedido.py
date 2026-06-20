from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.domain.models import ItemPedido, Pedido, Produto
from app.infrastructure.simulador_pagamento import solicitar_pagamento_mock


async def executar_fluxo_pedido(db: Session, dados_pedido):

    # Busca de produtos
    for item in dados_pedido.itens:
        produto_db = db.query(Produto).filter(Produto.id == item.produto_id).first()

        # Erro de produto não cadastrado
        if not produto_db:
            raise HTTPException(
                status_code=404,
                detail=f"O produto com ID {item.produto_id} não foi encontrado no cardápio."
            )

        # Erro de produto sem estoque
        if produto_db.estoque_disponivel < item.quantidade:
            raise HTTPException(
                status_code=409,
                detail=f"Estoque insuficiente para o item: {produto_db.nome}. Disponível: {produto_db.estoque_disponivel}"
            )

    # Novo pedido
    novo_pedido = Pedido(
        cliente_id=dados_pedido.cliente_id,
        canal_pedido=dados_pedido.canal_pedido,
        valor_total=dados_pedido.valor_total,
        status="AGUARDANDO_PAGAMENTO"
    )

    db.add(novo_pedido)
    db.commit()
    db.refresh(novo_pedido)

    for item in dados_pedido.itens:
        # Busca do produto pra atualizar o estoque
        produto_db = db.query(Produto).filter(Produto.id == item.produto_id).first()
        produto_db.estoque_disponivel -= item.quantidade
        novo_item = ItemPedido(
            pedido_id=novo_pedido.id,
            produto_id=item.produto_id,
            quantidade=item.quantidade,
            preco_unitario=item.preco_unitario
        )
        db.add(novo_item)

    db.commit()

    # Integrando com pagamento
    print(f"Solicitando autorização de pagamento para o pedido {novo_pedido.id}...")
    resultado = await solicitar_pagamento_mock(novo_pedido.valor_total, novo_pedido.id)

    # Status final
    if resultado["sucesso"]:
        novo_pedido.status = "COZINHA"
    else:
        novo_pedido.status = "CANCELADO"
        # Coloca o item de novo no estoque pq foi cancelado
        for item in dados_pedido.itens:
            produto_db = db.query(Produto).filter(Produto.id == item.produto_id).first()
            produto_db.estoque_disponivel += item.quantidade
        print(f"Pedido {novo_pedido.id} cancelado. Motivo: {resultado.get('motivo')}")

    db.commit()
    db.refresh(novo_pedido)

    return novo_pedido, resultado
