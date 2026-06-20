from typing import List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.application.processar_pedido import executar_fluxo_pedido
from app.domain.models import CanalPedido, Pedido, Produto
from app.infrastructure.database import get_db

router = APIRouter()

# modelos
class ModeloDoItem(BaseModel):
    produto_id: int
    quantidade: int
    preco_unitario: float

class DadosNovoPedido(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    cliente_id: int
    canal_pedido: CanalPedido = Field(alias="canalPedido")
    itens: List[ModeloDoItem]
    valor_total: float

class ProdutoBase(BaseModel):
    nome: str
    descricao: str
    preco: float
    estoque_disponivel: int

# para simular a validação
async def verificar_permissao_admin(authorization: Optional[str] = Query(None, description="Digite: Bearer TOKEN_ADMIN")):
    #Simulando token JWT e ADMIN.
    if authorization != "Bearer TOKEN_ADMIN":
        raise HTTPException(
            status_code=403,
            detail="Acesso negado: Perfil de Administrador exigido."
        )
    return "admin"

async def verificar_permissao_cliente(authorization: Optional[str] = Query(None, description="Digite: Bearer TOKEN_CLIENTE")):

    # Verificando se é usuário autenticado.
    if not authorization or "Bearer" not in authorization:
        raise HTTPException(
            status_code=401,
            detail="Não autenticado. Token JWT ausente ou inválido."
        )
    return "cliente"

# Auth
@router.post("/auth/login", tags=["Autenticação"])
async def login():
    return {"accessToken": "token-simulado-jwt", "tokenType": "Bearer"}

# usuários
@router.get("/usuarios/perfil", tags=["Usuários"])
async def ver_perfil():
    return {"id": 1, "nome": "Cliente Teste", "email": "teste@email.com"}

# Unidades
@router.get("/unidades", tags=["Unidades"])
async def listar_unidades():
    return [{"id": 1, "nome": "Unidade Rio Sul", "cidade": "Rio de Janeiro"}]

# produtos - CRUD
@router.get("/produtos", tags=["Produtos"])
async def listar_cardapio(
    page: int = Query(1, ge=1), limit: int = Query(10, le=50),
    db: Session = Depends(get_db)
):
    offset = (page - 1) * limit
    return db.query(Produto).offset(offset).limit(limit).all()

@router.post("/produtos", status_code=201, tags=["Produtos"], dependencies=[Depends(verificar_permissao_admin)])
async def criar_produto(produto: ProdutoBase, db: Session = Depends(get_db)):
    novo_prod = Produto(**produto.model_dump())
    db.add(novo_prod)
    db.commit()
    db.refresh(novo_prod)
    return novo_prod

@router.get("/produtos/{id}", tags=["Produtos"])
async def detalhe_produto(id: int, db: Session = Depends(get_db)):
    produto = db.query(Produto).filter(Produto.id == id).first()
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado.")
    return produto

@router.put("/produtos/{id}", tags=["Produtos"], dependencies=[Depends(verificar_permissao_admin)])
async def atualizar_produto(id: int, dados: ProdutoBase, db: Session = Depends(get_db)):
    produto_db = db.query(Produto).filter(Produto.id == id).first()
    if not produto_db:
        raise HTTPException(status_code=404, detail="Produto não encontrado.")

    for key, value in dados.model_dump().items():
        setattr(produto_db, key, value)

    db.commit()
    db.refresh(produto_db)
    return produto_db

@router.delete("/produtos/{id}", status_code=204, tags=["Produtos"], dependencies=[Depends(verificar_permissao_admin)])
async def excluir_produto(id: int, db: Session = Depends(get_db)):
    produto_db = db.query(Produto).filter(Produto.id == id).first()
    if not produto_db:
        raise HTTPException(status_code=404, detail="Produto não encontrado.")

    db.delete(produto_db)
    db.commit()
    return None

# Estoque
@router.get("/estoque/{unidade_id}", tags=["Estoque"])
async def consultar_estoque(unidade_id: int, db: Session = Depends(get_db)):
    return {"unidade_id": unidade_id, "status": "Estoque validado pelo Sistema."}

# pedidos
@router.post("/pedidos", status_code=201, tags=["Pedidos"], dependencies=[Depends(verificar_permissao_cliente)])
async def criar_pedido(dados: DadosNovoPedido, db: Session = Depends(get_db)):
    pedido, resultado = await executar_fluxo_pedido(db, dados)
    return {"id": pedido.id, "status": pedido.status, "pagamento": resultado}

@router.get("/pedidos", tags=["Pedidos"])
async def listar_pedidos(canal: Optional[CanalPedido] = None, db: Session = Depends(get_db)):
    query = db.query(Pedido)
    if canal:
        query = query.filter(Pedido.canal_pedido == canal)
    return query.all()

# Pagamentos
@router.get("/pagamentos/{pedido_id}/status", tags=["Pagamentos"])
async def verificar_pagamento(pedido_id: int):
    return {"pedido_id": pedido_id, "gateway": "Simulador", "status": "Autorizado"}

# Fidelidade
@router.get("/fidelidade/saldo", tags=["Fidelidade"])
async def consultar_pontos():
    return {"cliente_id": 1, "pontos": 150, "categoria": "Ouro"}
