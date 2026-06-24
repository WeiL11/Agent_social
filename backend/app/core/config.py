from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = "dev"
    database_url: str = "postgresql+psycopg://app:app@localhost:5432/persona"
    # Comma-separated list of allowed frontend origins (web + app dev servers).
    cors_origins: str = "http://localhost:3000"

    # Supabase Auth. When jwt secret is set we verify HS256 tokens; otherwise
    # dev mode falls back to the X-Dev-User header (see core/security.py).
    supabase_jwt_secret: str | None = None
    supabase_project_url: str | None = None

    # Character flavor generation. "none" => deterministic templated stub.
    llm_provider: str = "none"

    # Gameplay config defaults (also overridable via game_config table / live-ops).
    character_slot_cap: int = 3
    facet_weight_threshold: int = 30

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
