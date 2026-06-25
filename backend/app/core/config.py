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
    owner_friend_cap: int = 100          # max accepted owner(user)-level friends
    character_friend_daily_limit: int = 2  # new character-level friends per character per day

    # Matchmaking weights (tunable later / via game_config). Default leans
    # "similarity with a little complementarity".
    match_w_similarity: float = 0.50
    match_w_traits: float = 0.25
    match_w_facet: float = 0.15
    match_w_complement: float = 0.10

    @property
    def match_weights(self) -> dict[str, float]:
        return {
            "similarity": self.match_w_similarity,
            "traits": self.match_w_traits,
            "facet": self.match_w_facet,
            "complement": self.match_w_complement,
        }

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
