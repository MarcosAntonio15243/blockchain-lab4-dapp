import json
import logging
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from web3 import Web3
from sqlalchemy.orm import Session

from backend.database import get_db

from backend.config import settings
from backend.schemas.consulta_documento import ConsultaResponse
from backend.schemas.registrar_documento import (
    DocumentoInput,
    DocumentoResponse,
    PerfilOnChain,
    MAPA_PERFIL_ONCHAIN_PARA_CONSULENTE,
)
from backend.schemas.dados_sensiveis import CadastrarDadosSensiveisInput

from backend.services.consulta_service import ConsultaService
from backend.services.registrar_documento_service import RegistrarDocumentoService
from backend.services.controle_acesso_service import ControleAcessoService
from backend.services.permissao_leitura_service import PermissaoLeituraService
from backend.services.dados_sensiveis_service import DadosSensiveisService
from backend.auth.security import obter_endereco_autenticado
from backend.database import get_db

router = APIRouter(prefix="/documentos", tags=["Documentos"])
logger = logging.getLogger(__name__)

ABI_PATH = Path(__file__).parent.parent / "abi" / "RegistroDocumentos.json"

with open(ABI_PATH, "r", encoding="utf-8") as arquivo:
    conteudo = json.load(arquivo)
    REGISTRO_DOCUMENTOS_ABI = conteudo.get("abi", conteudo)

# ABI do ControleAcesso, usado so para checar perfil (nao para escrever)
ABI_CONTROLE_ACESSO_PATH = Path(__file__).parent.parent / "abi" / "ControleAcesso.json"
with open(ABI_CONTROLE_ACESSO_PATH, "r", encoding="utf-8") as arquivo:
    conteudo_controle_acesso = json.load(arquivo)
    CONTROLE_ACESSO_ABI = conteudo_controle_acesso.get("abi", conteudo_controle_acesso)

w3_provider = Web3(Web3.HTTPProvider(settings.BLOCKCHAIN_RPC_URL))


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


def get_controle_acesso_service(
    db: Session = Depends(get_db)
) -> ControleAcessoService:
    if not w3_provider.is_connected():
        raise HTTPException(status_code=503, detail="Blockchain indisponível.")
    return ControleAcessoService(
        w3=w3_provider,
        contract_address=settings.ENDERECO_CONTROLE_ACESSO,
        abi=CONTROLE_ACESSO_ABI,
        private_key=settings.CHAVE_PRIVADA_ADMIN,
        db=db
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
    if perfil_atual != PerfilOnChain.VARA:
        raise HTTPException(status_code=403, detail="perfil nao autorizado para esta acao")
    return endereco


@router.get("", response_model=list[DocumentoResponse])
def listar_documentos(
    service: RegistrarDocumentoService = Depends(get_registro_documentos_service),
    endereco_autenticado: str = Depends(exigir_perfil_vara),
):
    try:
        return service.listar()
    except Exception as erro:
        logger.exception("Erro ao listar documentos")
        raise HTTPException(status_code=400, detail=str(erro))


@router.post("", response_model=DocumentoResponse)
def registrar_documento(
    requisicao: DocumentoInput,
    service: RegistrarDocumentoService = Depends(get_registro_documentos_service),
    endereco_autenticado: str = Depends(exigir_perfil_vara),
):
    try:
        return service.registrar(requisicao)
    except Exception as erro:
        logger.exception("Erro ao registrar documento")
        raise HTTPException(status_code=400, detail=str(erro))


# IMPORTANTE: /emitir precisa vir ANTES de /{doc_id}, senao o FastAPI
# interpreta "emitir" como se fosse um doc_id.
@router.post("/emitir", response_model=DocumentoResponse)
def emitir_documento(
    documento: DocumentoInput,
    dados_pessoais: CadastrarDadosSensiveisInput,
    service: RegistrarDocumentoService = Depends(get_registro_documentos_service),
    db: Session = Depends(get_db),
    endereco_autenticado: str = Depends(exigir_perfil_vara),
):
    """
    Registra o documento on-chain e grava os dados pessoais em uma unica
    chamada. Equivale a POST /documentos + POST /documentos/{id}/dados-sensiveis.

    Sem rollback: se a gravacao dos dados pessoais falhar, o registro on-chain
    permanece e a validacao passa a responder apenas no nivel basico. O doc_id
    vai para o log para permitir completar depois.

    O PDF continua sendo anexado por POST /documentos/{doc_id}/arquivo.
    """
    resultado = service.registrar(documento)
    doc_id = resultado["doc_id"]

    dados_pessoais.doc_id = doc_id
    try:
        DadosSensiveisService(db).cadastrar(dados_pessoais, criado_por=endereco_autenticado)
    except Exception:
        logger.exception(
            "Documento %s registrado on-chain, mas falhou ao gravar dados pessoais", doc_id
        )
        raise

    return resultado


@router.get("/{doc_id}", response_model=DocumentoResponse)
def consultar_documento(
    doc_id: str,
    service: RegistrarDocumentoService = Depends(get_registro_documentos_service),
    controle_acesso: ControleAcessoService = Depends(get_controle_acesso_service),
    endereco_autenticado: str = Depends(obter_endereco_autenticado),
    db: Session = Depends(get_db),
):
    try:
        perfil_onchain = controle_acesso.consultar_perfil(endereco_autenticado)

        if perfil_onchain != PerfilOnChain.VARA:
            perfil_consulente = MAPA_PERFIL_ONCHAIN_PARA_CONSULENTE.get(perfil_onchain)
            permissao_service = PermissaoLeituraService(db)
            pode_ler = permissao_service.pode_ler(doc_id, endereco_autenticado, perfil_consulente)
            if not pode_ler:
                raise HTTPException(status_code=403, detail="sem permissao para ler este documento")

        return service.consultar(doc_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Documento não encontrado.")
    except HTTPException:
        raise  # preserva o status_code original
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


@router.get("/{doc_id}/consultas", response_model=list[ConsultaResponse])
def listar_consultas(
    doc_id: str,
    perfil: str | None = None,
    apenas_ampliadas: bool | None = None,
    db: Session = Depends(get_db),
    endereco_autenticado: str = Depends(exigir_perfil_vara),
):
    return ConsultaService(db).listar_por_documento(doc_id, perfil, apenas_ampliadas)