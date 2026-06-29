from pathlib import Path

import pytest

from ingest.config import ConfigurationError, load_config

_VALID_TOML = b"""
[ingestion]
seasons = ["2023-24", "2024-25"]
rate_limit_delay_seconds = 0.6
max_retries = 3
batch_size = 500
"""


def _write_toml(tmp_path: Path, content: bytes) -> Path:
    p = tmp_path / "config.toml"
    p.write_bytes(content)
    return p


def test_load_valid_config(tmp_path: Path) -> None:
    cfg = load_config(_write_toml(tmp_path, _VALID_TOML))
    assert cfg.seasons == ["2023-24", "2024-25"]
    assert cfg.rate_limit_delay_seconds == 0.6
    assert cfg.max_retries == 3
    assert cfg.batch_size == 500


def test_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(ConfigurationError, match="not found"):
        load_config(tmp_path / "nonexistent.toml")


def test_missing_section_raises(tmp_path: Path) -> None:
    with pytest.raises(ConfigurationError, match=r"\[ingestion\]"):
        load_config(_write_toml(tmp_path, b"[other]\nkey = 1"))


def test_missing_seasons_raises(tmp_path: Path) -> None:
    toml = b"[ingestion]\nrate_limit_delay_seconds = 0.6\nmax_retries = 3\nbatch_size = 500\n"
    with pytest.raises(ConfigurationError, match="seasons"):
        load_config(_write_toml(tmp_path, toml))


def test_missing_rate_limit_raises(tmp_path: Path) -> None:
    toml = b'[ingestion]\nseasons = ["2024-25"]\nmax_retries = 3\nbatch_size = 500\n'
    with pytest.raises(ConfigurationError, match="rate_limit_delay_seconds"):
        load_config(_write_toml(tmp_path, toml))


def test_missing_max_retries_raises(tmp_path: Path) -> None:
    toml = b'[ingestion]\nseasons = ["2024-25"]\nrate_limit_delay_seconds = 0.6\nbatch_size = 500\n'
    with pytest.raises(ConfigurationError, match="max_retries"):
        load_config(_write_toml(tmp_path, toml))


def test_missing_batch_size_raises(tmp_path: Path) -> None:
    toml = b'[ingestion]\nseasons = ["2024-25"]\nrate_limit_delay_seconds = 0.6\nmax_retries = 3\n'
    with pytest.raises(ConfigurationError, match="batch_size"):
        load_config(_write_toml(tmp_path, toml))
