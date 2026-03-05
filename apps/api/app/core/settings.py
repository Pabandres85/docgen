from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import AnyHttpUrl
from typing import List

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    storage_root: str = "/data/storage"
    redis_url: str = "redis://localhost:6379/0"
    database_url: str = "sqlite:////data/storage/docgen.sqlite"

    cors_origins: str = "http://localhost:8501"  # comma-separated

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

settings = Settings()
