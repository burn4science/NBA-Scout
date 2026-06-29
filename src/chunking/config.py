from __future__ import annotations

import tomllib
from pathlib import Path

_REQUIRED_KEYS = {
    "chunking": ["max_tokens", "overlap_tokens", "tokenizer"],
}

_DEFAULT_CONFIG_PATH = Path(__file__).parent / "config.toml"


class ConfigurationError(ValueError):
    pass


class ChunkConfig:
    def __init__(self, data: dict) -> None:
        self._data = data

    @property
    def max_tokens(self) -> int:
        return int(self._data["chunking"]["max_tokens"])

    @property
    def overlap_tokens(self) -> int:
        return int(self._data["chunking"]["overlap_tokens"])

    @property
    def tokenizer(self) -> str:
        return str(self._data["chunking"]["tokenizer"])

    @property
    def merge_peers(self) -> bool:
        return bool(self._data["chunking"].get("merge_peers", True))


def load_config(path: Path | None = None) -> ChunkConfig:
    config_path = path or _DEFAULT_CONFIG_PATH
    try:
        with open(config_path, "rb") as f:
            data = tomllib.load(f)
    except FileNotFoundError as e:
        raise ConfigurationError(f"Config file not found: {config_path}") from e

    for section, keys in _REQUIRED_KEYS.items():
        if section not in data:
            raise ConfigurationError(f"Missing required config section: [{section}]")
        for key in keys:
            if key not in data[section]:
                raise ConfigurationError(f"Missing required config key: [{section}].{key}")

    return ChunkConfig(data)
