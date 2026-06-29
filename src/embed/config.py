from __future__ import annotations

import tomllib
from pathlib import Path

_REQUIRED_KEYS = {
    "embedding": ["model", "dimension", "timeout_seconds", "batch_size"],
}

_DEFAULT_CONFIG_PATH = Path(__file__).parent / "config.toml"


class ConfigurationError(ValueError):
    pass


class EmbedConfig:
    def __init__(self, data: dict) -> None:
        self._data = data

    @property
    def model(self) -> str:
        return str(self._data["embedding"]["model"])

    @property
    def dimension(self) -> int:
        return int(self._data["embedding"]["dimension"])

    @property
    def timeout_seconds(self) -> float:
        return float(self._data["embedding"]["timeout_seconds"])

    @property
    def batch_size(self) -> int:
        return int(self._data["embedding"]["batch_size"])


def load_config(path: Path | None = None) -> EmbedConfig:
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

    return EmbedConfig(data)
