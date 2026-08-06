import logging

from fastapi import Request
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from backend.api.registrar_documento import router as documentos_router
from backend.api.controle_acesso import router as acessos_router


app = FastAPI()
logger = logging.getLogger(__name__)


@app.exception_handler(Exception)
async def tratar_erro_interno(request: Request, erro: Exception):
    logger.exception("Erro interno em %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Erro interno no servidor."},
    )

app.include_router(documentos_router, prefix="/api/v1")
app.include_router(acessos_router, prefix="/api/v1")

@app.get("/")
def health_check():
    return {"status": "API operacional"}
