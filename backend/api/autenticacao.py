from fastapi import APIRouter
from pydantic import BaseModel

from backend.auth.security import gerar_nonce, montar_mensagem, verificar_assinatura, criar_token_sessao

router = APIRouter(prefix="/auth", tags=["autenticacao"])


class PedidoNonce(BaseModel):
    endereco: str


class PedidoVerificacao(BaseModel):
    endereco: str
    assinatura: str


@router.post("/nonce")
def solicitar_nonce(pedido: PedidoNonce):
    """Passo 1: frontend pede um nonce/mensagem para assinar."""
    mensagem = gerar_nonce(pedido.endereco)
    return {"mensagem": mensagem}


@router.post("/verificar")
def verificar_login(pedido: PedidoVerificacao):
    """Passo 2: frontend envia a assinatura; se valida, devolve o token de sessao."""
    autenticado = verificar_assinatura(pedido.endereco, pedido.assinatura)

    if not autenticado:
        return {"autenticado": False}

    token = criar_token_sessao(pedido.endereco)
    return {"autenticado": True, "token": token}