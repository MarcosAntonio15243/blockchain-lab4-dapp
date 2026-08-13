import logging

from fastapi import Request
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from backend.api.registrar_documento import router as documentos_router
from backend.api.controle_acesso import router as acessos_router
from backend.api.autenticacao import router as autenticacao_router
from backend.api.permissao_leitura import router as permissoes_router
from backend.api.dados_sensiveis import router as dados_sensiveis_router
from backend.api.validacao_publica import router as validacao_publica_router

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
logger = logging.getLogger(__name__)


@app.exception_handler(Exception)
async def tratar_erro_interno(request: Request, erro: Exception):
    logger.exception("Erro interno em %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Erro interno no servidor."},
    )

app.include_router(dados_sensiveis_router, prefix="/api/v1")
app.include_router(validacao_publica_router, prefix="/api/v1")
app.include_router(documentos_router, prefix="/api/v1")
app.include_router(acessos_router, prefix="/api/v1")
app.include_router(autenticacao_router, prefix="/api/v1")
app.include_router(permissoes_router, prefix="/api/v1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],   
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def health_check():
    return {"status": "API operacional"}
