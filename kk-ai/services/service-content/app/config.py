from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    VERSION: str = "0.1.0"
    PORT: int = 9009
    LLM_GATEWAY_URL: str = "http://localhost:9001"
    PROMPT_SERVICE_URL: str = "http://localhost:9004"
    ASSET_SERVICE_URL: str = "http://localhost:9006"
    DATA_SERVICE_URL: str = "http://localhost:9005"
    API_KEY: str = "kk-content-key"
    DB_PATH: str = "./data/content.db"

    class Config:
        env_file = ".env"

_settings = None

def get_settings():
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
