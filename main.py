from datetime import datetime

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, RedirectResponse

from app.api.rotas import router
from app.infrastructure.database import Base, engine

# Criação das tabelas no SQLite
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Sistema Raízes do Nordeste - API Back-end")

# Tratamento de erro
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "error": "ERRO_VALIDACAO",
            "message": "Dados inválidos ou campos obrigatórios ausentes.",
            "details": exc.errors(),
            "timestamp": datetime.now().isoformat(),
            "path": request.url.path
        }
    )

# Tratamento para outros erros HTTP do sistema
@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "ERRO_SISTEMA",
            "message": exc.detail,
            "details": [],
            "timestamp": datetime.now().isoformat(),
            "path": request.url.path
        }
    )

from sqlalchemy.orm import Session

from app.domain.models import Produto
from app.infrastructure.database import SessionLocal


def popular_banco_automaticamente():
    # Pro banco não ficar vazio. insiro alguns dados
    db: Session = SessionLocal()
    try:
        if db.query(Produto).count() == 0:
            print("Populando banco de dados com itens do cardápio...")
            itens_iniciais = [
                Produto(nome="Tapioca de Carne de Sol", descricao="Regional", preco=25.50, estoque_disponivel=10, unidade_id=1),
                Produto(nome="Suco de Caju", descricao="Natural 500ml", preco=12.00, estoque_disponivel=50, unidade_id=1),
                Produto(nome="Cuscuz Completo", descricao="Com ovo e queijo", preco=18.90, estoque_disponivel=5, unidade_id=1)
            ]
            db.add_all(itens_iniciais)
            db.commit()
            print("Carga inicial concluída com sucesso!")
    except Exception as e:
        print(f"Erro ao popular banco: {e}")
    finally:
        db.close()

# Crio as tabelas e uso a função de inserir dados
Base.metadata.create_all(bind=engine)
popular_banco_automaticamente()



# Redireciona a rota raiz direto para o Swagger
@app.get("/", include_in_schema=False)
async def raiz():
    return RedirectResponse(url="/docs")

# Registro das rotas
app.include_router(router, prefix="/api/v1")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
