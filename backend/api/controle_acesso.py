import json
from web3 import Web3
from pathlib import Path
from fastapi import APIRouter, HTTPException, Depends

from backend.api.registrar_documento import exigir_perfil_vara
from backend.config import settings
from backend.schemas.controle_acesso import DefinirPerfilSchema, DefinirPerfilResponse, ConsultarPerfilResponse
from backend.services.controle_acesso_service import ControleAcessoService
from backend.auth.security import obter_endereco_autenticado

router = APIRouter(prefix="/acessos", tags=["Controle de Acesso / Perfis"])

ABI_DIR = Path(__file__).parent.parent / "abi"
ABI_PATH = ABI_DIR / "ControleAcesso.json"

with open(ABI_PATH, "r") as f:
    conteudo = json.load(f)
    CONTROLE_ACESSO_ABI = conteudo.get("abi", conteudo)

w3_provider = Web3(Web3.HTTPProvider(settings.BLOCKCHAIN_RPC_URL))



def get_controle_acesso_service() -> ControleAcessoService:
    if not w3_provider.is_connected():
        raise HTTPException(status_code=503, detail="Blockchain indisponível.")
    return ControleAcessoService(
        w3=w3_provider,
        contract_address=settings.ENDERECO_CONTROLE_ACESSO,
        abi=CONTROLE_ACESSO_ABI,
        private_key=settings.CHAVE_PRIVADA_ADMIN,
    )


@router.post("/definir-perfil", response_model=DefinirPerfilResponse)
def definir_perfil(
    requisicao: DefinirPerfilSchema,
    service: ControleAcessoService = Depends(get_controle_acesso_service),
    endereco_autenticado: str = Depends(exigir_perfil_vara),  # <- protecao adicionada
):
    try:
        hash_tx = service.definir_perfil(requisicao.conta, requisicao.perfil)
        return DefinirPerfilResponse(
            sucesso=True,
            hash_transacao=hash_tx,
            mensagem="Perfil atualizado com sucesso!",
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/consultar-perfil/{conta}", response_model=ConsultarPerfilResponse)
def consultar_perfil(
    conta: str,
    service: ControleAcessoService = Depends(get_controle_acesso_service),
    endereco_autenticado: str = Depends(obter_endereco_autenticado),
):
    """
    Consulta qual o perfil atual de um endereço.
    Exige apenas estar autenticado (nao precisa ser administrador).
    """
    try:
        perfil = service.consultar_perfil(conta)
        return ConsultarPerfilResponse(
            conta=conta,
            perfil_enum=perfil,
        )
    except Exception as erro:
        raise HTTPException(status_code=400, detail=f"Erro ao consultar Blockchain: {str(erro)}")