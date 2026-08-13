from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

ENV_PATH = Path(__file__).parent / ".env"

BASE_DIR = Path(__file__).parent      
RAIZ = BASE_DIR.parent


class Settings(BaseSettings):


    CHAVE_PRIVADA_ADMIN: str
    ENDERECO_CONTROLE_ACESSO: str 
    ENDERECO_REGISTRO_DOCUMENTOS: str 
    JWT_SECRET_KEY: str


    BLOCKCHAIN_RPC_URL: str = "http://127.0.0.1:8545"
    DATABASE_URL: str = f"sqlite:///{RAIZ / 'banco.db'}"

    model_config = SettingsConfigDict(
        env_file=ENV_PATH,
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
