from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    BLOCKCHAIN_RPC_URL: str = "http://127.0.0.1:8545"
    
    CHAVE_PRIVADA_ADMIN: str = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
       
    ENDERECO_CONTROLE_ACESSO: str = "0x5FbDB2315678afecb367f032d93F642f64180aa3"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()