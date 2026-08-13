from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.dados_sensiveis import CategoriaDocumento
from backend.services.dados_sensiveis_service import DadosSensiveisService
from backend.services.registrar_documento_service import RegistrarDocumentoService
from backend.api.registrar_documento import get_registro_documentos_service  # reaproveita a factory existente

router = APIRouter(prefix="/validacao", tags=["Validação Pública (QR Code)"])


@router.get("/{doc_id}")
def validar_documento_publico(
    doc_id: str,
    db: Session = Depends(get_db),
    service: RegistrarDocumentoService = Depends(get_registro_documentos_service),
):
    """
    Rota publica, sem autenticacao — e o destino do QR Code impresso no
    alvara/termo. So expoe os campos explicitamente autorizados, nunca o
    processo judicial, pecas, relatorios, etc.
    """
    try:
        documento_onchain = service.consultar(doc_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Código de validação inválido.")

    dados_service = DadosSensiveisService(db)
    dados_pessoais = dados_service.obter_para_validacao_publica(doc_id)

    if dados_pessoais is None:
        raise HTTPException(
            status_code=404,
            detail="Documento existe on-chain, mas dados de validação ainda não foram cadastrados.",
        )

    resposta_base = {
        "situacao": documento_onchain["status"],
        "tipo_documento": documento_onchain["tipo_documento"],
        "orgao_emissor": documento_onchain["orgao_emissor"],
        "autoridade_signataria": documento_onchain["autoridade_signataria"],
        "codigo_validacao": doc_id,
        "data_hora_ultima_atualizacao": (
            documento_onchain["status_atualizado_em"] or documento_onchain["emitido_em"]
        ),
        "nome_crianca_adolescente": dados_pessoais["nome_crianca"],
    }

    if dados_pessoais["categoria"] == CategoriaDocumento.ALVARA_VIAGEM:
        resposta_base.update({
            "nome_acompanhante_autorizado": dados_pessoais["nome_acompanhante"],
            "destino_viagem": dados_pessoais["destino_viagem"],
            "periodo_validade": documento_onchain["valido_ate"],
        })

    elif dados_pessoais["categoria"] == CategoriaDocumento.TERMO_GUARDA:
        resposta_base.update({
            "nome_guardiao": dados_pessoais["nome_guardiao"],
            "data_emissao": documento_onchain["emitido_em"],
            "validade_vigencia": documento_onchain["valido_ate"],
            "nao_revogado_ou_substituido": documento_onchain["status"] not in ("Revogado", "Substituido"),
        })

    return resposta_base