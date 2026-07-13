import os

from pydantic_settings import BaseSettings, SettingsConfigDict

_DEV_SECRET = "change-me-in-production"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    env: str = "development"
    database_url: str = "postgresql+asyncpg://sedna:sedna@localhost:5432/sedna"
    secret_key: str = _DEV_SECRET
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 days
    # CORS — comma-separated list of allowed origins
    cors_origins: str = "http://localhost:5173,http://localhost:3000"
    # Email
    email_enabled: bool = False
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_tls: bool = True
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = "noreply@sedna.academy"
    app_url: str = "http://localhost:5173"

    @property
    def allowed_origins(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    def validate_production(self) -> None:
        if self.env == "production" and self.secret_key == _DEV_SECRET:
            raise ValueError(
                "SECRET_KEY must be changed from the default before running in production. "
                "Set a strong random value in your .env file."
            )


settings = Settings()
settings.validate_production()
