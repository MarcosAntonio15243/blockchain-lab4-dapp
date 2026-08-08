import secrets
import time
from datetime import datetime, timedelta

from eth_account.messages import encode_defunct
from eth_account import Account
from jose import jwt, JWTError
from fastapi import HTTPException, Header

from backend.config import settings

ALGORITHM = "HS256"
SESSAO_EXPIRA_MINUTOS = 30
NONCE_EXPIRA_SEGUNDOS = 300  # 5 minutos

# Prototipo: dict em memoria. Em producao, troque por Redis
# (ex: redis_client.setex(endereco, NONCE_EXPIRA_SEGUNDOS, nonce)).
_nonces_pendentes: dict[str, tuple[str, float]] = {}


def gerar_nonce(endereco: str) -> str:
    endereco = endereco.lower()
    nonce = secrets.token_hex(16)
    _nonces_pendentes[endereco] = (nonce, time.time())
    return nonce


def montar_mensagem(endereco: str, nonce: str) -> str:
    return (
        f"Confirme que voce controla esta carteira.\n"
        f"Endereco: {endereco}\n"
        f"Nonce: {nonce}"
    )


def verificar_assinatura(endereco: str, assinatura: str) -> bool:
    endereco = endereco.lower()

    pendente = _nonces_pendentes.get(endereco)
    if pendente is None:
        raise HTTPException(status_code=400, detail="nenhum nonce pendente para este endereco")

    nonce, criado_em = pendente

    if time.time() - criado_em > NONCE_EXPIRA_SEGUNDOS:
        del _nonces_pendentes[endereco]
        raise HTTPException(status_code=400, detail="nonce expirado, solicite um novo")

    mensagem = montar_mensagem(endereco, nonce)
    mensagem_codificada = encode_defunct(text=mensagem)

    endereco_recuperado = Account.recover_message(mensagem_codificada, signature=assinatura)
    autenticado = endereco_recuperado.lower() == endereco

    # nonce e de uso unico, some apos a tentativa (sucesso ou falha)
    del _nonces_pendentes[endereco]

    return autenticado


def criar_token_sessao(endereco: str) -> str:
    expira_em = datetime.utcnow() + timedelta(minutes=SESSAO_EXPIRA_MINUTOS)
    payload = {"sub": endereco.lower(), "exp": expira_em}
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=ALGORITHM)


def obter_endereco_autenticado(authorization: str = Header(...)) -> str:
    """Dependency: extrai e valida o JWT do header 'Authorization: Bearer <token>'."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="token ausente ou mal formatado")

    token = authorization.removeprefix("Bearer ").strip()

    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[ALGORITHM])
        endereco: str = payload.get("sub")
        if endereco is None:
            raise HTTPException(status_code=401, detail="token invalido")
        return endereco
    except JWTError:
        raise HTTPException(status_code=401, detail="token invalido ou expirado")