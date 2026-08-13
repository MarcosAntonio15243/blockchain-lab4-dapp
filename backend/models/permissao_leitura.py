import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from backend.database import Base


def _uuid_str() -> str:
    return str(uuid.uuid4())


class PermissaoLeitura(Base):
    """
    Concede a um perfil (ou a um endereco especifico) o direito de ler
    um documento especifico, com expiracao opcional.
    """
    __tablename__ = "permissoes_leitura"

    id = Column(String, primary_key=True, default=_uuid_str)
    doc_id = Column(String, nullable=False, index=True)

    # Preencha UM dos dois: permissao por perfil (mais comum) OU por endereco especifico
    perfil = Column(String, nullable=True, index=True)  # ex: "PoliciaFederal"
    endereco = Column(String, nullable=True, index=True)  # endereco especifico, lowercase

    concedido_por = Column(String, nullable=False)  # endereco de quem concedeu (deve ser Vara)
    concedido_em = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Tempo limite de visualizacao: apos essa data, a permissao para de valer.
    # Nulo = sem expiracao (permissao permanente ate ser revogada manualmente).
    expira_em = Column(DateTime(timezone=True), nullable=True)

    revogado = Column(DateTime(timezone=True), nullable=True)  # data em que foi revogada manualmente, se houver