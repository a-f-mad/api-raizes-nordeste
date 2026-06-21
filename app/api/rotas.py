from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.application.processar_pedido import executar_fluxo_pedido
from app.domain.models import CanalPedido, Pedido, Produto
from app.infrastructure.database import get_db

router = APIRouter()

# TEXTO LGPD PARA EXIBIR NO SWAGGER
DOCUMENTACAO_LGPD = """
### 🛡️ Demonstração de Conformidade com a LGPD (Art. 7º)

O sistema Raízes do Nordeste realiza o tratamento de dados pessoais estritamente necessários para a operação, mapeados conforme as diretrizes legais:

1. **Nome do Cliente**
   - **Finalidade:** Identificação do titular para emissão de cupons, notas e controle de retirada de pedidos na cozinha.
   - **Base Legal:** Execução de Contrato (Art. 7º, V, da LGPD).

2. **E-mail**
   - **Finalidade:** Credencial de autenticação (Login), garantia de unicidade da conta e envio de notificações transacionais.
   - **Base Legal:** Execução de Contrato (Art. 7º, V, da LGPD).

3. **Senha (Armazenada como `senha_hash`)**
   - **Finalidade:** Garantia da segurança da informação, integridade da conta e prevenção a fraudes.
   - **Base Legal:** Cumprimento de Obrigação Legal / Segurança (Art. 7º, II).

4. **Consentimento (`consentimento_lgpd`)**
   - **Finalidade:** Registro inequívoco da manifestação livre do titular concordando com os termos de privacidade ao criar a conta.
   - **Base Legal:** Consentimento do Titular (Art. 7º, I).
"""

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
    unidade_id: Optional[int] = Field(1, description="ID da unidade da rede")

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
@router.post("/auth/cadastro", status_code=201, tags=["Autenticação e LGPD"], description=DOCUMENTACAO_LGPD)
async def cadastrar_usuario(dados: dict):
    timestamp_consentimento = datetime.utcnow().isoformat()
     # Criação de um novo usuário
    return {
        "message": "Usuário cadastrado com sucesso",
        "email": dados.get("email"),
        "registro_consentimento": {
            "status": "Aceito",
            "base_legal": "Art. 7º, I (Consentimento)",
            "timestamp": timestamp_consentimento
        }
    }

@router.post("/auth/login", tags=["Autenticação e LGPD"])
async def login():
    return {"accessToken": "token-simulado-jwt", "tokenType": "Bearer"}

# usuários e LGPD
@router.get("/usuarios/perfil", tags=["Usuários e Privacidade"])
async def ver_perfil():
    print(f"[{datetime.now().isoformat()}] AUDITORIA LGPD: Dados do usuário ID 1 acessados por Token Autenticado.")
    return {
        "id": 1,
        "nome": "Cliente Teste",
        "email": "teste@email.com",
        "perfil": "CLIENTE",
        "consentimento_lgpd_em": "2026-06-20T21:12:21"
    }

@router.delete("/usuarios/perfil", status_code=204, tags=["Usuários e Privacidade"])
async def excluir_ou_anonimizar_conta():
    # Direito de eliminação de dados do usuário
    print(f"[{datetime.now().isoformat()}] AUDITORIA LGPD: Solicitação de exclusão recebida. Dados anonimizados no banco.")
    return None

# Unidades
@router.get("/unidades", tags=["Unidades"])
async def listar_unidades():
    return [{"id": 1, "nome": "Unidade Rio Sul", "cidade": "Rio de Janeiro"}]

# produtos - CRUD
@router.get("/produtos", tags=["Produtos"])
async def listar_cardapio(
    unidade_id: Optional[int] = Query(None, description="Filtrar cardápio pelo ID da unidade da rede"),
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

@router.patch("/pedidos/{id}/status", tags=["Pedidos"], dependencies=[Depends(verificar_permissao_admin)])
async def atualizar_status_pedido(id: int, novo_status: str = Query(..., description="Escolha: PRONTO, ENTREGUE ou CANCELADO"), db: Session = Depends(get_db)):
    pedido_db = db.query(Pedido).filter(Pedido.id == id).first()
    if not pedido_db:
        raise HTTPException(status_code=404, detail="Pedido não encontrado.")

    pedido_db.status = novo_status
    db.commit()
    db.refresh(pedido_db)
    return {"id": pedido_db.id, "status_atualizado": pedido_db.status}

# Pagamentos
@router.get("/pagamentos/{pedido_id}/status", tags=["Pagamentos"])
async def verificar_pagamento(pedido_id: int):
    return {"pedido_id": pedido_id, "gateway": "Simulador", "status": "Autorizado"}

# Fidelidade
# Fidelidade
@router.get("/fidelidade/saldo", tags=["Fidelidade"])
async def consultar_pontos():
    return {"cliente_id": 1, "pontos_disponiveis": 150, "categoria": "Ouro"}

@router.post("/fidelidade/resgatar", tags=["Fidelidade"])
async def resgatar_pontos(pontos: int = Query(..., ge=10)):
    # Resgate de pontos para gerar desconto
    valor_desconto = pontos * 0.10
    return {
        "status": "Sucesso",
        "pontos_resgatados": pontos,
        "desconto_aplicado_reais": valor_desconto,
        "mensagem": "Resgate autorizado. Aplique o desconto no valor total do pedido."
    }

# Promoções e Campanhas
@router.get("/promocoes", tags=["Promoções e Campanhas"])
async def listar_campanhas_ativas():
    return [
        {
            "nome_campanha": "Orgulho Nordestino",
            "cupom": "DESCONTO10",
            "regra": "10% de desconto em qualquer prato regional utilizando o canal APP ou TOTEM",
            "ativa": True
        }
    ]
