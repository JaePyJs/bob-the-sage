from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    deepl_api_key: str | None = None
    semantic_scholar_api_key: str | None = None
    gemini_api_key: str | None = None
    allowed_origins_raw: str = "http://localhost:3000"
    arxiv_delay_seconds: int = 5
    s2_requests_per_second: int = 1

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        env_prefix="",
        case_sensitive=False,
    )

    @property
    def allowed_origins(self) -> list[str]:
        raw = self.allowed_origins_raw or ""
        return [s.strip() for s in raw.split(",") if s.strip()]

    @property
    def s2_enabled(self) -> bool:
        """Semantic Scholar is optional. When no key, run arXiv-only mode."""
        return bool(self.semantic_scholar_api_key)


settings = Settings()