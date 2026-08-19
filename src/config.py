from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

# Para que encuentre el .env en la ruta parent
BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    temp_path: str
    llm_provider: str
    llm_model: str
    api_key: str
    model_config = SettingsConfigDict(env_file=f"{BASE_DIR}/.env", extra="ignore")


settings: Settings = Settings()
