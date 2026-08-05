from fastapi import FastAPI
from backend.api.registrar_documento import router as documentos_router
from backend.api.controle_acesso import router as acessos_router


app = FastAPI()

app.include_router(documentos_router, prefix="/api/v1")
app.include_router(acessos_router, prefix="/api/v1")

@app.get("/")
def health_check():
    return {"status": "API operacional"}