import hashlib
from fastapi import APIRouter, Depends, File, HTTPException, Header, UploadFile
from sqlalchemy.orm import Session
from typing import Optional
from backend.database import get_db
from backend.models.dados_sensiveis import CategoriaDocumento
from backend.services.dados_sensiveis_service import DadosSensiveisService
from backend.services.permissao_leitura_service import PermissaoLeituraService
from backend.services.registrar_documento_service import RegistrarDocumentoService
from backend.services.controle_acesso_service import ControleAcessoService
from backend.services.consulta_service import ConsultaService
from backend.schemas.registrar_documento import PerfilOnChain, MAPA_PERFIL_ONCHAIN_PARA_CONSULENTE
from backend.api.registrar_documento import (
    get_registro_documentos_service,
    get_controle_acesso_service,
)
from backend.auth.security import obter_endereco_autenticado
from backend.auth.security import obter_endereco_autenticado, obter_endereco_opcional

router = APIRouter(prefix="/validacao", tags=["Validação Pública (QR Code)"])


def _tem_acesso_ampliado(
    doc_id: str,
    endereco: Optional[str],
    db: Session,
    controle_acesso: ControleAcessoService,
) -> bool:
    """Vara sempre ve tudo; demais precisam de permissao para ESTE documento."""
    if endereco is None:
        return False

    perfil_onchain = controle_acesso.consultar_perfil(endereco)
    if perfil_onchain == PerfilOnChain.VARA:
        return True

    perfil_consulente = MAPA_PERFIL_ONCHAIN_PARA_CONSULENTE.get(perfil_onchain)
    return PermissaoLeituraService(db).pode_ler(doc_id, endereco, perfil_consulente)


@router.get("/{doc_id}")
def validar_documento_publico(
    doc_id: str,
    db: Session = Depends(get_db),
    service: RegistrarDocumentoService = Depends(get_registro_documentos_service),
    controle_acesso: ControleAcessoService = Depends(get_controle_acesso_service),
    endereco: Optional[str] = Depends(obter_endereco_opcional),
):
    """
    Destino do QR Code impresso no alvara/termo.

    Nivel basico (sem login): status e metadados do ato, todos ja registrados
    on-chain. Nao expoe dados pessoais.

    Nivel ampliado (autenticado com permissao para este documento): acrescenta
    os dados pessoais necessarios a conferencia, conforme o perfil de acesso
    do consulente.
    """
    try:
        documento = service.consultar(doc_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Código de validação inválido.")

    resposta = {
        "situacao": documento["status"],
        "tipo_documento": documento["tipo_documento"],
        "orgao_emissor": documento["orgao_emissor"],
        "autoridade_signataria": documento["autoridade_signataria"],
        "periodo_validade": documento["valido_ate"],
        "codigo_validacao": doc_id,
        "data_hora_ultima_atualizacao": (
            documento["status_atualizado_em"] or documento["emitido_em"]
        ),
        "nao_revogado_ou_substituido": documento["status"] not in ("Revogado", "Substituido"),
        "acesso_ampliado": False,
    }

    ampliado = _tem_acesso_ampliado(doc_id, endereco, db, controle_acesso)

    perfil_nome = None
    if endereco:
        perfil_nome = controle_acesso.consultar_perfil(endereco).name

    dados_pessoais = (
        DadosSensiveisService(db).obter_para_validacao_publica(doc_id) if ampliado else None
    )

    if dados_pessoais is not None:
        resposta["acesso_ampliado"] = True
        resposta["nome_crianca_adolescente"] = dados_pessoais["nome_crianca"]

        if dados_pessoais["categoria"] == CategoriaDocumento.ALVARA_VIAGEM:
            resposta["nome_acompanhante_autorizado"] = dados_pessoais["nome_acompanhante"]
            resposta["destino_viagem"] = dados_pessoais["destino_viagem"]
        elif dados_pessoais["categoria"] == CategoriaDocumento.TERMO_GUARDA:
            resposta["nome_guardiao"] = dados_pessoais["nome_guardiao"]
            resposta["data_emissao"] = documento["emitido_em"]

    ConsultaService(db).registrar(
        doc_id=doc_id,
        endereco=endereco,
        perfil=perfil_nome,
        acesso_ampliado=resposta["acesso_ampliado"],
    )

    return resposta


@router.post("/{doc_id}/conferir-integridade")
async def conferir_integridade(
    doc_id: str,
    arquivo: UploadFile = File(...),
    service: RegistrarDocumentoService = Depends(get_registro_documentos_service),
):
    """
    Confere se o PDF apresentado corresponde ao documento registrado on-chain.
    Publica de proposito: quem tem o arquivo ja tem o conteudo, e a resposta
    e apenas confere/nao confere. Nao expoe nenhum dado novo.
    """
    try:
        documento = service.consultar(doc_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Código de validação inválido.")

    conteudo = await arquivo.read()
    hash_apresentado = "0x" + hashlib.sha256(conteudo).hexdigest()

    integro = hash_apresentado.lower() == documento["hash_documento"].lower()

    return {
        "integro": integro,
        "situacao": documento["status"],
        "hash_apresentado": hash_apresentado,
        "hash_registrado": documento["hash_documento"],
    }