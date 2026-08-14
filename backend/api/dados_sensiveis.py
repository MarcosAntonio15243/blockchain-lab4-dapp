from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import io

from backend.database import get_db
from backend.services.dados_sensiveis_service import DadosSensiveisService
from backend.schemas.dados_sensiveis import CadastrarDadosSensiveisInput, DadosSensiveisResponse
from backend.api.registrar_documento import exigir_perfil_vara

router = APIRouter(prefix="/documentos", tags=["Dados Sensíveis"])


@router.post("/{doc_id}/dados-sensiveis", response_model=DadosSensiveisResponse)
def cadastrar_dados_sensiveis(
    doc_id: str,
    dados: CadastrarDadosSensiveisInput,
    db: Session = Depends(get_db),
    endereco_autenticado: str = Depends(exigir_perfil_vara),
):
    if dados.doc_id != doc_id:
        raise HTTPException(status_code=400, detail="doc_id do corpo nao bate com o da URL")

    service = DadosSensiveisService(db)
    try:
        registro = service.cadastrar(dados, criado_por=endereco_autenticado)
    except ValueError as erro:
        raise HTTPException(status_code=409, detail=str(erro))

    return DadosSensiveisResponse(
        doc_id=registro.doc_id,
        categoria=registro.categoria,
        possui_arquivo=registro.arquivo_conteudo_cripto is not None,
        criado_em=registro.criado_em.isoformat(),
    )


TIPOS_PERMITIDOS = {"application/pdf"}
TAMANHO_MAXIMO_BYTES = 10 * 1024 * 1024  # 10 MB


@router.post("/{doc_id}/arquivo")
async def anexar_arquivo(
    doc_id: str,
    arquivo: UploadFile = File(...),
    db: Session = Depends(get_db),
    endereco_autenticado: str = Depends(exigir_perfil_vara),
):
    if arquivo.content_type not in TIPOS_PERMITIDOS:
        raise HTTPException(status_code=415, detail="Apenas arquivos PDF são aceitos.")

    conteudo = await arquivo.read()

    if len(conteudo) > TAMANHO_MAXIMO_BYTES:
        raise HTTPException(status_code=413, detail="Arquivo excede o tamanho máximo de 10MB.")

    service = DadosSensiveisService(db)
    try:
        service.anexar_arquivo(
            doc_id=doc_id,
            conteudo=conteudo,
            nome_original=arquivo.filename,
            content_type=arquivo.content_type,
        )
    except KeyError:
        raise HTTPException(
            status_code=404,
            detail="Cadastre os dados sensíveis (POST /dados-sensiveis) antes de anexar o arquivo.",
        )

    return {"sucesso": True, "arquivo_nome": arquivo.filename}


@router.get("/{doc_id}/arquivo")
def baixar_arquivo(
    doc_id: str,
    db: Session = Depends(get_db),
    endereco_autenticado: str = Depends(exigir_perfil_vara),
):
    service = DadosSensiveisService(db)
    try:
        conteudo, nome_original, content_type = service.obter_arquivo(doc_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Arquivo não encontrado para este documento.")

    return StreamingResponse(
        io.BytesIO(conteudo),
        media_type=content_type or "application/pdf",
        headers={"Content-Disposition": f'inline; filename="{nome_original or "documento.pdf"}"'},
    )