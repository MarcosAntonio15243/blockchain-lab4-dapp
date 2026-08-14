from pydantic import BaseModel, Field
from enum import Enum

class PerfilEnum(int, Enum):
    NENHUM = 0
    VARA = 1
    POLICIA_FEDERAL = 2
    COMPANHIA_AEREA = 3
    COMPANHIA_RODOVIARIA = 4
    CARTORIO = 5
    CONSELHO_TUTELAR = 6
    CASA_ACOLHIMENTO = 7
    ESCOLA = 8
    HOSPITAL = 9
    MINISTERIO_PUBLICO = 10
    DEFENSORIA_PUBLICA = 11
    OUTRO_ORGAO_PUBLICO = 12

class DefinirPerfilSchema(BaseModel):
    conta: str = Field(..., description="Endereço 0x... da carteira na blockchain")
    perfil: PerfilEnum = Field(..., description="Perfil a ser atribuído (1 a 4)")
    nome: str = Field(..., description="Nome da instituição em questão")

class DefinirPerfilResponse(BaseModel):
    sucesso: bool
    hash_transacao: str
    mensagem: str

class ConsultarPerfilResponse(BaseModel):
    conta: str
    perfil_enum: int