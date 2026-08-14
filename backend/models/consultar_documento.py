import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime, Boolean
from backend.database import Base


def _uuid_str() -> str:
    return str(uuid.uuid4())


class ConsultaDocumento(Base):
    """
    Trilha de consultas por QR Code, exigida pela proposta: data e hora da
    consulta e identificacao institucional do consulente, quando aplicavel.

    Consulta anonima e registrada com endereco nulo — o documento preve o
    caso ("quando aplicavel").
    """
    __tablename__ = "consultas_documentos"

    id = Column(String, primary_key=True, default=_uuid_str)
    doc_id = Column(String, nullable=False, index=True)

    endereco = Column(String, nullable=True, index=True)   # None = anonimo
    nome_instituicao = Column(String, nullable=True)       # copiado no momento da consulta
    perfil = Column(String, nullable=True)

    acesso_ampliado = Column(Boolean, nullable=False, default=False)
    consultado_em = Column(DateTime(timezone=True),
                           default=lambda: datetime.now(timezone.utc), index=True)