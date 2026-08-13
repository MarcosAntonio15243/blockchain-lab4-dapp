from datetime import datetime, timezone

from sqlalchemy.orm import Session

from backend.models.dados_sensiveis import DadosSensiveisDocumento, CategoriaDocumento
from backend.schemas.dados_sensiveis import CadastrarDadosSensiveisInput
from backend.security.criptografia import criptografar, descriptografar, criptografar_bytes, descriptografar_bytes

class DadosSensiveisService:
    def __init__(self, db: Session):
        self.db = db

    def cadastrar(self, dados: CadastrarDadosSensiveisInput, criado_por: str) -> DadosSensiveisDocumento:
        existente = (
            self.db.query(DadosSensiveisDocumento)
            .filter(DadosSensiveisDocumento.doc_id == dados.doc_id)
            .first()
        )
        if existente is not None:
            raise ValueError("ja existem dados sensiveis cadastrados para este doc_id")

        registro = DadosSensiveisDocumento(
            doc_id=dados.doc_id,
            categoria=dados.categoria,
            nome_crianca_cripto=criptografar(dados.nome_crianca),
            nome_acompanhante_cripto=criptografar(dados.nome_acompanhante),
            destino_viagem_cripto=criptografar(dados.destino_viagem),
            nome_guardiao_cripto=criptografar(dados.nome_guardiao),
            criado_por=criado_por.lower(),
        )
        self.db.add(registro)
        self.db.commit()
        self.db.refresh(registro)
        return registro

    def obter_para_validacao_publica(self, doc_id: str) -> dict | None:
        """
        Retorna apenas os campos pessoais autorizados para a pagina publica de
        validacao (QR Code). Nao inclui o arquivo (o arquivo nao faz parte da
        lista de campos exibidos publicamente, conforme os requisitos).
        """
        registro = (
            self.db.query(DadosSensiveisDocumento)
            .filter(DadosSensiveisDocumento.doc_id == doc_id)
            .first()
        )
        if registro is None:
            return None

        base = {
            "categoria": registro.categoria,
            "nome_crianca": descriptografar(registro.nome_crianca_cripto),
        }

        if registro.categoria == CategoriaDocumento.ALVARA_VIAGEM:
            base["nome_acompanhante"] = descriptografar(registro.nome_acompanhante_cripto)
            base["destino_viagem"] = descriptografar(registro.destino_viagem_cripto)
        elif registro.categoria == CategoriaDocumento.TERMO_GUARDA:
            base["nome_guardiao"] = descriptografar(registro.nome_guardiao_cripto)

        return base

    def anexar_arquivo(self, doc_id: str, conteudo: bytes, nome_original: str, content_type: str) -> None:
        registro = (
            self.db.query(DadosSensiveisDocumento)
            .filter(DadosSensiveisDocumento.doc_id == doc_id)
            .first()
        )
        if registro is None:
            raise KeyError(doc_id)

        registro.arquivo_conteudo_cripto = criptografar_bytes(conteudo)
        registro.arquivo_nome_original = nome_original
        registro.arquivo_content_type = content_type
        self.db.commit()

    def obter_arquivo(self, doc_id: str) -> tuple[bytes, str | None, str | None]:
        registro = (
            self.db.query(DadosSensiveisDocumento)
            .filter(DadosSensiveisDocumento.doc_id == doc_id)
            .first()
        )
        if registro is None or registro.arquivo_conteudo_cripto is None:
            raise KeyError(doc_id)

        conteudo = descriptografar_bytes(registro.arquivo_conteudo_cripto)
        return conteudo, registro.arquivo_nome_original, registro.arquivo_content_type