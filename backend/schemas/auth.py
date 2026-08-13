from pydantic import BaseModel

class PedidoNonce(BaseModel):
    endereco: str

class PedidoVerificacao(BaseModel):
    endereco: str
    assinatura: str

class PedidoNonceResponse(BaseModel):
    mensagem: str

class PedidoVerificacaoResponse(BaseModel):
    autenticado: bool
    token: str | None = None