from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.api.registrar_documento import exigir_perfil_vara
from backend.database import get_db
from backend.schemas.permissao_leitura import (
    ConcederPermissaoInput,
    PermissaoLeituraResponse,
    RevogarPermissaoInput,
)
from backend.services.permissao_leitura_service import PermissaoLeituraService
from backend.auth.security import obter_endereco_autenticado

router = APIRouter(prefix="/permissoes", tags=["Permissoes de Leitura"])


@router.post("", response_model=PermissaoLeituraResponse)
def conceder_permissao(
    dados: ConcederPermissaoInput,
    db: Session = Depends(get_db),
    endereco_autenticado: str = Depends(exigir_perfil_vara),  # so Vara concede acesso
):
    service = PermissaoLeituraService(db)
    permissao = service.conceder(dados, concedido_por=endereco_autenticado)
    return permissao


@router.delete("")
def revogar_permissao(
    dados: RevogarPermissaoInput,
    db: Session = Depends(get_db),
    endereco_autenticado: str = Depends(exigir_perfil_vara),
):
    service = PermissaoLeituraService(db)
    try:
        service.revogar(dados.permissao_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Permissão não encontrada.")
    return {"sucesso": True}


@router.get("/{doc_id}", response_model=list[PermissaoLeituraResponse])
def listar_permissoes(
    doc_id: str,
    db: Session = Depends(get_db),
    endereco_autenticado: str = Depends(exigir_perfil_vara),
):
    service = PermissaoLeituraService(db)
    return service.listar_por_documento(doc_id)