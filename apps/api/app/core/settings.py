from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    storage_root: str = "/data/storage"
    redis_url: str = "redis://localhost:6379/0"
    database_url: str = "sqlite:////data/storage/docgen.sqlite"
    max_upload_mb: int = 20
    libreoffice_timeout_seconds: int = 120
    auto_create_tables: bool = False
    log_level: str = "INFO"
    environment: str = "dev"
    trusted_hosts: str = "localhost,127.0.0.1,api,testserver"
    rate_limit_enabled: bool = True
    rate_limit_requests: int = 120
    rate_limit_window_seconds: int = 60

    cors_origins: str = "http://localhost:8501"  # comma-separated

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def trusted_hosts_list(self) -> List[str]:
        return [h.strip() for h in self.trusted_hosts.split(",") if h.strip()]

settings = Settings()
