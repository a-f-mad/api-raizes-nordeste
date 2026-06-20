import enum
from datetime import datetime

from sqlalchemy import (Column, DateTime, Enum, Float, ForeignKey, Integer,
                        String)
from sqlalchemy.orm import relationship

from app.infrastructure.database import Base


class CanalPedido(str, enum.Enum):
    APP = "APP"
    TOTEM = "TOTEM"
    BALCAO = "BALCAO"
    PICKUP = "PICKUP"
    WEB = "WEB"

# LGPD
class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    senha_hash = Column(String(255), nullable=False)
    perfil = Column(String(20), default="CLIENTE")
    consentimento_lgpd = Column(DateTime, default=datetime.utcnow)

# Produto
class Produto(Base):
    __tablename__ = "produtos"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False)
    descricao = Column(String(255))
    preco = Column(Float, nullable=False)
    estoque_disponivel = Column(Integer, default=0)

# Entidade Pedido
class Pedido(Base):
    __tablename__ = "pedidos"

    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(Integer, ForeignKey("usuarios.id"))

    canal_pedido = Column(Enum(CanalPedido), nullable=False)

    status = Column(String(30), default="AGUARDANDO_PAGAMENTO")
    valor_total = Column(Float, default=0.0)
    data_criacao = Column(DateTime, default=datetime.utcnow)

    # Relacionamentos
    itens = relationship("ItemPedido", back_populates="pedido")

# Itens do Pedido
class ItemPedido(Base):
    __tablename__ = "itens_pedido"

    id = Column(Integer, primary_key=True, index=True)
    pedido_id = Column(Integer, ForeignKey("pedidos.id"))
    produto_id = Column(Integer)
    quantidade = Column(Integer, nullable=False)
    preco_unitario = Column(Float, nullable=False)

    pedido = relationship("Pedido", back_populates="itens")
