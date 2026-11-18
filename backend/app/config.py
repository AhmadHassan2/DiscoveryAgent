"""Application configuration loaded from environment variables (and an optional .env file).

No secrets are hardcoded. Every AI/integration setting is optional: when the LLM or the
embedding endpoint is not configured, the platform runs in deterministic demo mode.
"""
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=(".env", "../.env"), env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Idea Discovery"
    environment: str = "local"

    # Database ---------------------------------------------------------------------------
    database_url: str = "postgresql+psycopg://localhost:5432/idea_discovery"

    # LLM provider: "auto" | "anthropic" | "openai_compatible" | "none" ----------------------
    # auto -> Anthropic if Anthropic credentials are present, else the OpenAI-compatible
    # gateway if configured, else deterministic mode.
    llm_provider: str = "auto"
    # Claude (official Anthropic SDK). Credentials are resolved by the SDK itself:
    # ANTHROPIC_API_KEY, ANTHROPIC_AUTH_TOKEN, or an `ant auth login` profile.
    anthropic_model: str = "claude-sonnet-5-5"
    anthropic_effort: str = "low"

    # LLM (OpenAI-compatible, e.g. an internal enterprise gateway) -------------------------
    llm_base_url: str | None = None
    llm_api_key: str | None = None
    llm_model: str | None = None
    llm_timeout_seconds: float = 30.0
    llm_temperature: float = 0.0

    # Embeddings (OpenAI-compatible /embeddings). Falls back to the local concept embedder.
    embedding_base_url: str | None = None
    embedding_api_key: str | None = None
    embedding_model: str | None = None
    embedding_dimensions: int = 384

    # Connectors ---------------------------------------------------------------------------
    connector_timeout_seconds: float = 5.0
    # Simulated network latency for mock connectors (ms). Clearly a simulation; set 0 to disable.
    mock_connector_latency_ms: int = 350
    # Comma-separated list of sources to force-fail (for demonstrating degraded behaviour).
    fail_sources: str = ""

    # CORS -----------------------------------------------------------------------------------
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    # Seed -----------------------------------------------------------------------------------
    auto_seed: bool = True

    # Requester identity placeholder until enterprise SSO is integrated.
    default_requester: str = Field(default="demo.user@northbridge.example")

    @property
    def openai_compatible_configured(self) -> bool:
        return bool(self.llm_base_url and self.llm_model)

    @property
    def anthropic_credentials_present(self) -> bool:
        import os
        from pathlib import Path

        if os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN"):
            return True
        return (Path.home() / ".config" / "anthropic").exists()

    @property
    def resolved_llm_provider(self) -> str:
        choice = self.llm_provider.lower().strip()
        if choice in ("none", "deterministic", "off"):
            return "none"
        if choice == "anthropic":
            return "anthropic"
        if choice in ("openai", "openai_compatible", "gateway"):
            return "openai_compatible" if self.openai_compatible_configured else "none"
        if self.anthropic_credentials_present:
            return "anthropic"
        if self.openai_compatible_configured:
            return "openai_compatible"
        return "none"

    @property
    def remote_embeddings_enabled(self) -> bool:
        return bool(self.embedding_base_url and self.embedding_model)

    @property
    def failed_source_set(self) -> set[str]:
        return {s.strip().lower() for s in self.fail_sources.split(",") if s.strip()}

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
