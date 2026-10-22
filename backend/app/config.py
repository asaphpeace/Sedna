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
    # Text-to-speech (AWS Polly) — see docs/DEPLOYMENT.md
    aws_region: str = "us-east-1"
    polly_voice_id: str = "Joanna"
    # Google sign-in — off while google_client_id is empty. The client ID comes
    # from an OAuth client (type "Web application") in Google Cloud.
    google_client_id: str = ""
    # Google Workspace domains whose people may join without an invite, as
    # Sedna staff learners. Comma-separated.
    google_staff_domains: str = "sedna.com"
    # Customer Workspace domains allowed to use Google sign-in. Invite-only:
    # the person must already have an account. Empty for now.
    google_customer_domains: str = ""
    # Jira (VMS support cases) — optional; the ticket sync is off without a token.
    # Put these in backend/.env, never in code.
    jira_base_url: str = ""
    jira_email: str = ""
    jira_api_token: str = ""
    jira_project: str = "DSD"
    jira_customer_field: str = "customfield_10047"  # "Customer" picklist: {"value": "Name|<option id>"}

    @property
    def staff_google_domains(self) -> set[str]:
        return {d.strip().lower() for d in self.google_staff_domains.split(",") if d.strip()}

    @property
    def customer_google_domains(self) -> set[str]:
        return {d.strip().lower() for d in self.google_customer_domains.split(",") if d.strip()}

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
