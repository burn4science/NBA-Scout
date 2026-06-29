from pathlib import Path

import pytest

from chunking.config import ConfigurationError, load_config

_VALID_TOML = b"""
[chunking]
max_tokens = 512
overlap_tokens = 64
tokenizer = "sentence-transformers/all-MiniLM-L6-v2"
merge_peers = true
"""


def _write(tmp_path: Path, content: bytes) -> Path:
    p = tmp_path / "config.toml"
    p.write_bytes(content)
    return p


def test_load_valid_config(tmp_path: Path) -> None:
    cfg = load_config(_write(tmp_path, _VALID_TOML))
    assert cfg.max_tokens == 512
    assert cfg.overlap_tokens == 64
    assert cfg.tokenizer == "sentence-transformers/all-MiniLM-L6-v2"
    assert cfg.merge_peers is True


def test_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(ConfigurationError, match="not found"):
        load_config(tmp_path / "nope.toml")


def test_missing_section_raises(tmp_path: Path) -> None:
    with pytest.raises(ConfigurationError, match=r"\[chunking\]"):
        load_config(_write(tmp_path, b"[other]\nkey = 1"))


def test_missing_key_raises(tmp_path: Path) -> None:
    with pytest.raises(ConfigurationError, match="max_tokens"):
        load_config(_write(tmp_path, b'[chunking]\noverlap_tokens = 64\ntokenizer = "x"\n'))
