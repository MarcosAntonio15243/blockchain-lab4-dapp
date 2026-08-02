from pydantic import BaseModel, Field
from enum import Enum

class PerfilEnum(int, Enum):
    NENHUM = 0
    VARA = 1
    POLICIA_FEDERAL = 2
    COMPANHIA_AEREA = 3
    CONSELHO_TUTELAR = 4

class DefinirPerfilSchema(BaseModel):
    conta: str = Field(..., description="Endereço 0x... da carteira na blockchain")
    perfil: PerfilEnum = Field(..., description="Perfil a ser atribuído (1 a 4)")

class DefinirPerfilResponse(BaseModel):
    sucesso: bool
    hash_transacao: str
    mensagem: str

class ConsultarPerfilResponse(BaseModel):
    conta: str
    perfil_enum: int