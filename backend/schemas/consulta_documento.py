from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ConsultaResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    id: str
    doc_id: str = Field(..., alias="docId")
    endereco: Optional[str] = None
    nome_instituicao: Optional[str] = Field(None, alias="nomeInstituicao")
    perfil: Optional[str] = None
    acesso_ampliado: bool = Field(..., alias="acessoAmpliado")
    consultado_em: datetime = Field(..., alias="consultadoEm")