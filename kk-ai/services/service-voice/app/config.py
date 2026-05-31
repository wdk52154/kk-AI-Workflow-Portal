from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    VERSION: str = "0.1.0"
    PORT: int = 9008
    LLM_GATEWAY_URL: str = "http://localhost:9001"
    RAG_SERVICE_URL: str = "http://localhost:9002"
    MEMORY_SERVICE_URL: str = "http://localhost:9003"
    PROMPT_SERVICE_URL: str = "http://localhost:9004"
    DATA_SERVICE_URL: str = "http://localhost:9005"
    ASSET_SERVICE_URL: str = "http://localhost:9006"
    MCP_HUB_URL: str = "http://localhost:8000"
    API_KEY: str = "kk-voice-key"
    DB_PATH: str = "./data/voice.db"

    class Config:
        env_file = ".env"

_settings = None

def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
