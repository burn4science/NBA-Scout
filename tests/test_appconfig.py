import pytest
from pydantic import ValidationError

from appconfig.models import ChunkingConfig, EmbeddingConfig, IngestionConfig
from appconfig.settings import ConfigError, _ensure_dimension_matches, settings


def test_settings_loaded_from_config_folder() -> None:
    # The module-level `settings` reads the real config/ TOML files at import.
    assert settings.ingestion.seasons  # non-empty list of seasons
    assert all(isinstance(s, str) for s in settings.ingestion.seasons)
    assert isinstance(settings.ingestion.max_retries, int)
    assert settings.chunking.max_tokens == 512
    assert settings.chunking.merge_peers is True
    assert settings.embedding.model
    assert settings.embedding.dimension == 768


def test_secrets_section_present() -> None:
    # Secrets are exposed as distinct typed fields, defaulting to None when unset.
    secrets = settings.secrets
    assert hasattr(secrets, "database_url")
    assert hasattr(secrets, "embedding_base_url")
    assert hasattr(secrets, "embedding_api_key")


def test_missing_required_key_raises() -> None:
    with pytest.raises(ValidationError):
        IngestionConfig(rate_limit_delay_seconds=0.6, max_retries=3, batch_size=500)
    with pytest.raises(ValidationError):
        ChunkingConfig(overlap_tokens=64, tokenizer="x")  # missing max_tokens
    with pytest.raises(ValidationError):
        EmbeddingConfig(model="m", timeout_seconds=30, batch_size=32)  # missing dimension


def test_dimension_guard_passes_when_equal() -> None:
    _ensure_dimension_matches(768, 768)


def test_dimension_guard_fails_on_drift() -> None:
    with pytest.raises(ConfigError, match="dimension"):
        _ensure_dimension_matches(384, 768)
