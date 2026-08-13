import uuid
from datetime import datetime, timezone
from enum import Enum as PyEnum

from sqlalchemy import Column, String, DateTime, Enum, LargeBinary
from backend.database import Base


def _uuid_str() -> str:
    return str(uuid.uuid4())


class CategoriaDocumento(str, PyEnum):
    ALVARA_VIAGEM = "alvara_viagem"
    TERMO_GUARDA = "termo_guarda"


class DadosSensiveisDocumento(Base):
    """
    Dados pessoais e o arquivo do documento, guardados fora da blockchain e
    criptografados em repouso. Ligados ao doc_id que ja existe on-chain.
    """
    __tablename__ = "dados_sensiveis_documentos"

    id = Column(String, primary_key=True, default=_uuid_str)
    doc_id = Column(String, nullable=False, unique=True, index=True)
    categoria = Column(Enum(CategoriaDocumento), nullable=False)

    # Comuns aos dois tipos de documento
    nome_crianca_cripto = Column(LargeBinary, nullable=False)

    # Especificos de alvara de viagem
    nome_acompanhante_cripto = Column(LargeBinary, nullable=True)
    destino_viagem_cripto = Column(LargeBinary, nullable=True)

    # Especifico de termo de guarda
    nome_guardiao_cripto = Column(LargeBinary, nullable=True)

    # O arquivo do documento em si (PDF), criptografado
    arquivo_conteudo_cripto = Column(LargeBinary, nullable=True)
    arquivo_nome_original = Column(String, nullable=True)
    arquivo_content_type = Column(String, nullable=True)

    criado_por = Column(String, nullable=False)  # endereco de quem cadastrou (deve ser Vara)
    criado_em = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))