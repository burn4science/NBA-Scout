from pathlib import Path

import pytest

from embed.config import ConfigurationError, load_config

_VALID_TOML = b"""
[embedding]
model = "text-embedding-embeddinggemma-300m"
dimension = 768
timeout_seconds = 30
batch_size = 32
"""


def _write(tmp_path: Path, content: bytes) -> Path:
    p = tmp_path / "config.toml"
    p.write_bytes(content)
    return p


def test_load_valid_config(tmp_path: Path) -> None:
    cfg = load_config(_write(tmp_path, _VALID_TOML))
    assert cfg.model == "text-embedding-embeddinggemma-300m"
    assert cfg.dimension == 768
    assert cfg.timeout_seconds == 30.0
    assert cfg.batch_size == 32


def test_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(ConfigurationError, match="not found"):
        load_config(tmp_path / "nope.toml")


def test_missing_section_raises(tmp_path: Path) -> None:
    with pytest.raises(ConfigurationError, match=r"\[embedding\]"):
        load_config(_write(tmp_path, b"[other]\nkey = 1"))


def test_missing_dimension_raises(tmp_path: Path) -> None:
    toml = b'[embedding]\nmodel = "m"\ntimeout_seconds = 30\nbatch_size = 32\n'
    with pytest.raises(ConfigurationError, match="dimension"):
        load_config(_write(tmp_path, toml))
