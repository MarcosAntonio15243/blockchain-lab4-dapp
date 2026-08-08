import json
import logging
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from web3 import Web3

from backend.config import settings
from backend.schemas.registrar_documento import (
    DocumentoInput,
    DocumentoResponse,
    HashTransacaoResponse,
    PerfilConsulente,
    ResultadoValidacaoResponse,
)
from backend.services.registrar_documento_service import RegistrarDocumentoService
from backend.services.controle_acesso_service import ControleAcessoService
from backend.auth.security import obter_endereco_autenticado


router = APIRouter(prefix="/documentos", tags=["Documentos"])
logger = logging.getLogger(__name__)

ABI_PATH = (
    Path(__file__).parent.parent.parent
    / "artifacts"
    / "RegistroDocumentos.sol"
    / "RegistroDocumentos.json"
)
with open(ABI_PATH, "r", encoding="utf-8") as arquivo:
    conteudo = json.load(arquivo)
    REGISTRO_DOCUMENTOS_ABI = conteudo.get("abi", conteudo)

# ABI do ControleAcesso, usado so para checar perfil (nao para escrever)
ABI_CONTROLE_ACESSO_PATH = Path(__file__).parent.parent / "abi" / "ControleAcesso.json"
with open(ABI_CONTROLE_ACESSO_PATH, "r", encoding="utf-8") as arquivo:
    conteudo_controle_acesso = json.load(arquivo)
    CONTROLE_ACESSO_ABI = conteudo_controle_acesso.get("abi", conteudo_controle_acesso)

w3_provider = Web3(Web3.HTTPProvider(settings.BLOCKCHAIN_RPC_URL))

# Enum StatusDocumento/Perfil do seu ControleAcesso.sol: Nenhum=0, Vara=1, PoliciaFederal=2, ...
PERFIL_VARA = 1


def get_registro_documentos_service() -> RegistrarDocumentoService:
    if not w3_provider.is_connected():
        logger.error("Blockchain indisponível em %s", settings.BLOCKCHAIN_RPC_URL)
        raise HTTPException(status_code=503, detail="Blockchain indisponível.")
    if not settings.ENDERECO_REGISTRO_DOCUMENTOS:
        logger.error("ENDERECO_REGISTRO_DOCUMENTOS não configurado")
        raise HTTPException(
            status_code=500,
            detail="ENDERECO_REGISTRO_DOCUMENTOS não configurado.",
        )

    return RegistrarDocumentoService(
        w3=w3_provider,
        contract_address=settings.ENDERECO_REGISTRO_DOCUMENTOS,
        abi=REGISTRO_DOCUMENTOS_ABI,
        private_key=settings.CHAVE_PRIVADA_ADMIN,
    )


def get_controle_acesso_service() -> ControleAcessoService:
    if not w3_provider.is_connected():
        raise HTTPException(status_code=503, detail="Blockchain indisponível.")
    return ControleAcessoService(
        w3=w3_provider,
        contract_address=settings.ENDERECO_CONTROLE_ACESSO,
        abi=CONTROLE_ACESSO_ABI,
        private_key=settings.CHAVE_PRIVADA_ADMIN,
    )


def exigir_perfil_vara(
    endereco: str = Depends(obter_endereco_autenticado),
    controle_acesso: ControleAcessoService = Depends(get_controle_acesso_service),
) -> str:
    """
    So libera acoes de escrita (registrar/revogar/substituir) se o endereco
    autenticado por assinatura possuir o perfil Vara on-chain.
    """
    perfil_atual = controle_acesso.consultar_perfil(endereco)
    if perfil_atual != PERFIL_VARA:
        raise HTTPException(status_code=403, detail="perfil nao autorizado para esta acao")
    return endereco


@router.get("", response_model=list[DocumentoResponse])
def listar_documentos(
    service: RegistrarDocumentoService = Depends(get_registro_documentos_service),
    endereco_autenticado: str = Depends(obter_endereco_autenticado),
):
    try:
        return service.listar()
    except Exception as erro:
        logger.exception("Erro ao listar documentos")
        raise HTTPException(status_code=400, detail=str(erro))


@router.post("", response_model=HashTransacaoResponse)
def registrar_documento(
    requisicao: DocumentoInput,
    service: RegistrarDocumentoService = Depends(get_registro_documentos_service),
    endereco_autenticado: str = Depends(exigir_perfil_vara),
):
    try:
        documento = service.registrar(requisicao)
        return {"hash_transacao": documento["hash_transacao"]}
    except Exception as erro:
        logger.exception("Erro ao registrar documento")
        raise HTTPException(status_code=400, detail=str(erro))


@router.get("/{doc_id}", response_model=DocumentoResponse)
def consultar_documento(
    doc_id: str,
    service: RegistrarDocumentoService = Depends(get_registro_documentos_service),
    endereco_autenticado: str = Depends(obter_endereco_autenticado),
):
    try:
        return service.consultar(doc_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Documento não encontrado.")
    except Exception as erro:
        logger.exception("Erro ao consultar documento %s", doc_id)
        raise HTTPException(status_code=400, detail=str(erro))


@router.post("/{doc_id}/revogar", response_model=DocumentoResponse)
def revogar_documento(
    doc_id: str,
    service: RegistrarDocumentoService = Depends(get_registro_documentos_service),
    endereco_autenticado: str = Depends(exigir_perfil_vara),
):
    try:
        return service.revogar(doc_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Documento não encontrado.")
    except Exception as erro:
        logger.exception("Erro ao revogar documento %s", doc_id)
        raise HTTPException(status_code=400, detail=str(erro))


@router.post("/{doc_id}/substituir", response_model=DocumentoResponse)
def substituir_documento(
    doc_id: str,
    requisicao: DocumentoInput,
    service: RegistrarDocumentoService = Depends(get_registro_documentos_service),
    endereco_autenticado: str = Depends(exigir_perfil_vara),
):
    try:
        return service.substituir(doc_id, requisicao)
    except KeyError:
        raise HTTPException(status_code=404, detail="Documento não encontrado.")
    except Exception as erro:
        logger.exception("Erro ao substituir documento %s", doc_id)
        raise HTTPException(status_code=400, detail=str(erro))


@router.get("/{doc_id}/validar", response_model=ResultadoValidacaoResponse)
def validar_documento(
    doc_id: str,
    perfil: PerfilConsulente = Query(...),
    service: RegistrarDocumentoService = Depends(get_registro_documentos_service),
    endereco_autenticado: str = Depends(obter_endereco_autenticado),
):
    try:
        return service.validar(doc_id, perfil)
    except KeyError:
        return {"existe": False}
    except Exception as erro:
        logger.exception("Erro ao validar documento %s", doc_id)
        raise HTTPException(status_code=400, detail=str(erro))