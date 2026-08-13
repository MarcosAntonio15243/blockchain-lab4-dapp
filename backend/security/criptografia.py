from cryptography.fernet import Fernet, InvalidToken
from fastapi import HTTPException

from backend.config import settings

_fernet = Fernet(settings.CHAVE_CRIPTOGRAFIA_DADOS_SENSIVEIS.encode())


def criptografar(valor: str | None) -> bytes | None:
    if valor is None:
        return None
    return _fernet.encrypt(valor.encode("utf-8"))


def descriptografar(valor_criptografado: bytes | None) -> str | None:
    if valor_criptografado is None:
        return None
    try:
        return _fernet.decrypt(bytes(valor_criptografado)).decode("utf-8")
    except InvalidToken:
        raise HTTPException(status_code=500, detail="Falha ao decifrar dado sensível.")


def criptografar_bytes(conteudo: bytes | None) -> bytes | None:
    """Versao para dados binarios (ex: PDF), sem round-trip por string/hex."""
    if conteudo is None:
        return None
    return _fernet.encrypt(conteudo)


def descriptografar_bytes(conteudo_criptografado: bytes | None) -> bytes | None:
    if conteudo_criptografado is None:
        return None
    try:
        return _fernet.decrypt(bytes(conteudo_criptografado))
    except InvalidToken:
        raise HTTPException(status_code=500, detail="Falha ao decifrar arquivo.")