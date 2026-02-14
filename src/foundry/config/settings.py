from pydantic_settings import BaseSettings
from pydantic import ConfigDict

class Settings(BaseSettings):

    model_config = ConfigDict(env_file=".env", env_file_encoding="utf-8")

    google_api_key: str
    gemini_api_key: str
    claude_api_key: str
    environment: str = "development"

settings = Settings()