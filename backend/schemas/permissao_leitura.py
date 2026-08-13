from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from backend.schemas.registrar_documento import PerfilConsulente


class ConcederPermissaoInput(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    doc_id: str = Field(..., alias="docId")
    perfil: Optional[PerfilConsulente] = None
    endereco: Optional[str] = None
    expira_em: Optional[datetime] = Field(None, alias="expiraEm")  # tempo limite de visualizacao

    @model_validator(mode="after")
    def validar_alvo_unico(self):
        if not self.perfil and not self.endereco:
            raise ValueError("informe 'perfil' ou 'endereco' para conceder a permissao")
        if self.perfil and self.endereco:
            raise ValueError("informe apenas um: 'perfil' OU 'endereco', nao os dois")
        return self


class PermissaoLeituraResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    doc_id: str = Field(..., alias="docId")
    perfil: Optional[str] = None
    endereco: Optional[str] = None
    concedido_por: str = Field(..., alias="concedidoPor")
    concedido_em: datetime = Field(..., alias="concedidoEm")
    expira_em: Optional[datetime] = Field(None, alias="expiraEm")
    revogado: Optional[datetime] = None


class RevogarPermissaoInput(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    permissao_id: str = Field(..., alias="permissaoId")