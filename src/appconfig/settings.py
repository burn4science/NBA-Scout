from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv
from loguru import logger
from pydantic import Field
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    TomlConfigSettingsSource,
)

from appconfig.models import ChunkingConfig, EmbeddingConfig, IngestionConfig
from db.models import EMBEDDING_DIM

# config/ lives at the repo root and is copied verbatim into the image
# (`COPY config/ ./config/`), so the same relative resolution works locally and
# in the container (WORKDIR /app).
_REPO_ROOT = Path(__file__).resolve().parents[2]
_CONFIG_DIR = _REPO_ROOT / "config"
_INGESTION_TOML = _CONFIG_DIR / "ingestion.toml"
_EMBEDDING_TOML = _CONFIG_DIR / "embedding.toml"


class ConfigError(RuntimeError):
    """Raised when configuration is missing, malformed, or inconsistent."""


# Load .env once, centrally, so both os.environ-based readers (e.g. the db
# engines) and the Secrets model below see the same values. A missing file is a
# no-op: in Docker the values arrive as real environment variables.
load_dotenv(_REPO_ROOT / ".env")


class Secrets(BaseSettings):
    """Environment-specific secrets and endpoints — sourced from the environment
    / .env, never from committed TOML. Optional at load time; consuming code
    fails loudly at point of use if a value it needs is absent."""

    model_config = SettingsConfigDict(extra="ignore", case_sensitive=False)

    database_url: str | None = None
    migration_database_url: str | None = None
    app_database_url: str | None = None
    embedding_base_url: str | None = None
    embedding_api_key: str | None = None
    host_shared_data_dir: str | None = None


class Settings(BaseSettings):
    """Single source of truth for all configuration. Tunables come from the TOML
    files under config/; secrets come from the environment. Loaded once at import
    and exposed as the module-level ``settings``."""

    model_config = SettingsConfigDict(extra="ignore")

    ingestion: IngestionConfig
    chunking: ChunkingConfig
    embedding: EmbeddingConfig
    secrets: Secrets = Field(default_factory=Secrets)

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        # Highest priority first: init args win (tests can override), then the two
        # TOML files supply the tunable sections. Env/dotenv populate the nested
        # Secrets via its own default_factory.
        return (
            init_settings,
            TomlConfigSettingsSource(settings_cls, toml_file=_INGESTION_TOML),
            TomlConfigSettingsSource(settings_cls, toml_file=_EMBEDDING_TOML),
            env_settings,
            dotenv_settings,
            file_secret_settings,
        )


def _ensure_dimension_matches(config_dim: int, schema_dim: int) -> None:
    """Fail loudly if the configured embedding dimension diverges from the vector
    column width baked into the database schema."""
    if config_dim != schema_dim:
        raise ConfigError(
            f"embedding.dimension ({config_dim}) does not match the database schema's "
            f"EMBEDDING_DIM ({schema_dim}). Update config/embedding.toml to match the "
            f"vector(N) column, or migrate the schema."
        )


def _build_settings() -> Settings:
    try:
        loaded = Settings()
    except FileNotFoundError as exc:
        raise ConfigError(f"Configuration file not found: {exc}") from exc

    # Guard the schema coupling at startup (see EMBEDDING_DIM in src/db/models.py).
    _ensure_dimension_matches(loaded.embedding.dimension, EMBEDDING_DIM)
    logger.debug(
        "Configuration loaded: {} ingestion seasons, embedding model '{}' (dim {})",
        len(loaded.ingestion.seasons),
        loaded.embedding.model,
        loaded.embedding.dimension,
    )
    return loaded


settings = _build_settings()
