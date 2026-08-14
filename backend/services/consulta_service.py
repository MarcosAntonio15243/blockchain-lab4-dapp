import logging
from typing import Optional

from sqlalchemy.orm import Session

from backend.models.consultar_documento import ConsultaDocumento
from backend.models.instituicao import Instituicao

logger = logging.getLogger(__name__)


class ConsultaService:
    def __init__(self, db: Session):
        self.db = db

    def registrar(
        self,
        doc_id: str,
        endereco: Optional[str],
        perfil: Optional[str],
        acesso_ampliado: bool,
    ) -> None:
        """
        Grava a consulta. Nunca levanta excecao: falha de auditoria nao pode
        impedir alguem de validar um alvara no balcao do aeroporto.
        """
        try:
            nome = None
            if endereco:
                instituicao = (
                    self.db.query(Instituicao)
                    .filter(Instituicao.endereco == endereco.lower())
                    .first()
                )
                nome = instituicao.nome if instituicao else None

            self.db.add(ConsultaDocumento(
                doc_id=doc_id,
                endereco=endereco.lower() if endereco else None,
                nome_instituicao=nome,
                perfil=perfil,
                acesso_ampliado=acesso_ampliado,
            ))
            self.db.commit()
        except Exception:
            logger.exception("Falha ao registrar consulta do documento %s", doc_id)
            self.db.rollback()

    def listar_por_documento(
        self,
        doc_id: str,
        perfil: Optional[str] = None,
        apenas_ampliadas: Optional[bool] = None,
    ) -> list[ConsultaDocumento]:
        consulta = self.db.query(ConsultaDocumento).filter(
            ConsultaDocumento.doc_id == doc_id
        )
        if perfil is not None:
            consulta = consulta.filter(ConsultaDocumento.perfil == perfil)
        if apenas_ampliadas is not None:
            consulta = consulta.filter(ConsultaDocumento.acesso_ampliado == apenas_ampliadas)
        return consulta.order_by(ConsultaDocumento.consultado_em.desc()).all()