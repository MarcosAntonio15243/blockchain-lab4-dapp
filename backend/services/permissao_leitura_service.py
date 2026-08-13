from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session

from backend.models.permissao_leitura import PermissaoLeitura
from backend.schemas.permissao_leitura import ConcederPermissaoInput
from backend.schemas.registrar_documento import PerfilConsulente


class PermissaoLeituraService:
    def __init__(self, db: Session):
        self.db = db

    def conceder(self, dados: ConcederPermissaoInput, concedido_por: str) -> PermissaoLeitura:
        permissao = PermissaoLeitura(
            doc_id=dados.doc_id,
            perfil=dados.perfil.value if dados.perfil else None,
            endereco=dados.endereco.lower() if dados.endereco else None,
            concedido_por=concedido_por.lower(),
            expira_em=dados.expira_em,
        )
        self.db.add(permissao)
        self.db.commit()
        self.db.refresh(permissao)
        return permissao

    def revogar(self, permissao_id: str) -> None:
        permissao = self.db.get(PermissaoLeitura, permissao_id)
        if permissao is None:
            raise KeyError(permissao_id)
        permissao.revogado = datetime.now(timezone.utc)
        self.db.commit()

    def listar_por_documento(self, doc_id: str) -> list[PermissaoLeitura]:
        return (
            self.db.query(PermissaoLeitura)
            .filter(PermissaoLeitura.doc_id == doc_id)
            .order_by(PermissaoLeitura.concedido_em.desc())
            .all()
        )

    def pode_ler(self, doc_id: str, endereco: str, perfil_onchain: Optional[PerfilConsulente]) -> bool:
        """
        Verifica se existe permissao valida (nao revogada, nao expirada) para
        o endereco especifico OU para o perfil dele.
        """
        agora = datetime.now(timezone.utc)
        endereco = endereco.lower()

        filtros = [PermissaoLeitura.doc_id == doc_id, PermissaoLeitura.revogado.is_(None)]

        condicao_expiracao = or_(
            PermissaoLeitura.expira_em.is_(None),
            PermissaoLeitura.expira_em > agora,
        )

        condicoes_alvo = [PermissaoLeitura.endereco == endereco]
        if perfil_onchain is not None:
            condicoes_alvo.append(PermissaoLeitura.perfil == perfil_onchain.value)

        permissao = (
            self.db.query(PermissaoLeitura)
            .filter(*filtros, condicao_expiracao, or_(*condicoes_alvo))
            .first()
        )
        return permissao is not None