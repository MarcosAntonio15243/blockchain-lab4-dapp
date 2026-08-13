import base64
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from backend.models.dados_sensiveis import CategoriaDocumento


class CadastrarDadosSensiveisInput(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    doc_id: str = Field(..., alias="docId")
    categoria: CategoriaDocumento

    nome_crianca: str = Field(..., alias="nomeCrianca")

    # Alvara de viagem
    nome_acompanhante: Optional[str] = Field(None, alias="nomeAcompanhante")
    destino_viagem: Optional[str] = Field(None, alias="destinoViagem")

    # Termo de guarda
    nome_guardiao: Optional[str] = Field(None, alias="nomeGuardiao")

    @model_validator(mode="after")
    def validar_campos_por_categoria(self):
        if self.categoria == CategoriaDocumento.ALVARA_VIAGEM:
            if not self.nome_acompanhante or not self.destino_viagem:
                raise ValueError(
                    "alvara de viagem exige 'nomeAcompanhante' e 'destinoViagem'"
                )
        if self.categoria == CategoriaDocumento.TERMO_GUARDA:
            if not self.nome_guardiao:
                raise ValueError("termo de guarda exige 'nomeGuardiao'")
        return self


class DadosSensiveisResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    doc_id: str = Field(..., alias="docId")
    categoria: CategoriaDocumento
    possui_arquivo: bool = Field(..., alias="possuiArquivo")
    criado_em: str = Field(..., alias="criadoEm")