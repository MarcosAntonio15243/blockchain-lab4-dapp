from enum import Enum
from enum import IntEnum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

class PerfilOnChain(IntEnum):
    # Espelha o enum Perfil do contrato ControleAcesso.sol. A ordem importa.
    NENHUM = 0
    VARA = 1
    POLICIA_FEDERAL = 2
    COMPANHIA_AEREA = 3
    CONSELHO_TUTELAR = 4


class PerfilConsulente(str, Enum):
    POLICIA_FEDERAL = "PoliciaFederal"
    COMPANHIA_AEREA = "CompanhiaAerea"
    CONSELHO_TUTELAR = "ConselhoTutelar"

MAPA_PERFIL_ONCHAIN_PARA_CONSULENTE: dict[PerfilOnChain, PerfilConsulente] = {
    PerfilOnChain.POLICIA_FEDERAL: PerfilConsulente.POLICIA_FEDERAL,
    PerfilOnChain.COMPANHIA_AEREA: PerfilConsulente.COMPANHIA_AEREA,
    PerfilOnChain.CONSELHO_TUTELAR: PerfilConsulente.CONSELHO_TUTELAR,
}

class DocumentoInput(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    hash_documento: str = Field(..., alias="hashDocumento")
    tipo_documento: str = Field(..., alias="tipoDocumento")
    orgao_emissor: str = Field(..., alias="orgaoEmissor")
    autoridade_signataria: str = Field(..., alias="autoridadeSignataria")
    hash_assinatura: Optional[str] = Field(None, alias="hashAssinatura")
    valido_ate: Optional[str] = Field(None, alias="validoAte")


class DocumentoResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    doc_id: str = Field(..., alias="docId")
    hash_documento: str = Field(..., alias="hashDocumento")
    tipo_documento: str = Field(..., alias="tipoDocumento")
    orgao_emissor: str = Field(..., alias="orgaoEmissor")
    autoridade_signataria: Optional[str] = Field(None, alias="autoridadeSignataria")
    hash_assinatura: Optional[str] = Field(None, alias="hashAssinatura")
    emitido_em: str = Field(..., alias="emitidoEm")
    valido_ate: Optional[str] = Field(None, alias="validoAte")
    status: str
    substituido_por: Optional[str] = Field(None, alias="substituidoPor")
    status_atualizado_em: Optional[str] = Field(None, alias="statusAtualizadoEm")
    hash_transacao: Optional[str] = Field(None, alias="hashTransacao")
    existe: bool = True


class HashTransacaoResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    hash_transacao: str = Field(..., alias="hashTransacao")


class ResultadoValidacaoResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    existe: bool
    status: Optional[str] = None
    campos_visiveis: Optional[dict[str, str]] = Field(None, alias="camposVisiveis")
