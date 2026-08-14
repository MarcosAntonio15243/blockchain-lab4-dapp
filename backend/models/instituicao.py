import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime
from backend.database import Base


def _uuid_str() -> str:
    return str(uuid.uuid4())


class Instituicao(Base):
    """
    Registro do nome real por tras de um endereco com perfil institucional.
    Uso exclusivamente para auditoria/rastreabilidade — NAO controla
    permissoes, que continuam sendo por perfil (PermissaoLeitura.perfil).
    """
    __tablename__ = "instituicoes"

    id = Column(String, primary_key=True, default=_uuid_str)
    endereco = Column(String, nullable=False, unique=True, index=True)
    nome = Column(String, nullable=False)  # ex: "Companhia Aerea X - Filial Recife"
    cadastrado_por = Column(String, nullable=False)
    cadastrado_em = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))