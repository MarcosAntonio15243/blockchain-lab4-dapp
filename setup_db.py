# setup_db.py
from backend.database import Base, engine
from backend.models.permissao_leitura import PermissaoLeitura
from backend.models.dados_sensiveis import DadosSensiveisDocumento
from backend.models.consulta_documento import ConsultaDocumento

Base.metadata.create_all(bind=engine)
print("Tabelas criadas.")