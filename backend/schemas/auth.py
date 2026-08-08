from pydantic import BaseModel


class PedidoNonceSchema(BaseModel):
    conta: str


class PedidoNonceResponse(BaseModel):
    mensagem: str


class PedidoVerificacaoSchema(BaseModel):
    conta: str
    assinatura: str


class PedidoVerificacaoResponse(BaseModel):
    autenticado: bool
    token: str | None = None