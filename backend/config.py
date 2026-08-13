from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

ENV_PATH = Path(__file__).parent / ".env"

class Settings(BaseSettings):
    BLOCKCHAIN_RPC_URL: str = "http://127.0.0.1:8545"

    CHAVE_PRIVADA_ADMIN: str = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"

    ENDERECO_CONTROLE_ACESSO: str = "0x5FbDB2315678afecb367f032d93F642f64180aa3"

    ENDERECO_REGISTRO_DOCUMENTOS: str = "0x9fE46736679d2D9a65F0992F2272dE9f3c7fa6e0"

    JWT_SECRET_KEY: str = "troque-por-um-valor-aleatorio-forte"

    DATABASE_URL: str

    model_config = SettingsConfigDict(
        env_file=ENV_PATH,
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
