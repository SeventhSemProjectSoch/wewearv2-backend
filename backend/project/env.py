from pathlib import Path
from secrets import token_urlsafe

from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict


class Environment(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")
    DEBUG: bool = True
    POSTGRES_HOST: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_DB: str = "wewear"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_PASSWORD_FILE: Path | None = None
    POSTGRES_PORT: int = 5432
    ALLOWED_HOSTS: str = "*"
    CSRF_TRUSTED_ORIGINS: str = "http://127.0.0.1:8000"
    SECRET_KEY: str = token_urlsafe(127)
    SECRET_KEY_FILE: Path | None = None


ENV = Environment()
