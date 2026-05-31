from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    VERSION: str = "0.1.0"
    PORT: int = 9011
    ASSET_SERVICE_URL: str = "http://localhost:9006"
    DATA_SERVICE_URL: str = "http://localhost:9005"
    API_KEY: str = "kk-live-key"
    DB_PATH: str = "./data/live.db"
    VIDEO_STORAGE: str = "./data/videos"

    class Config:
        env_file = ".env"

_settings = None

def get_settings():
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
