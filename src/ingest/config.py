from __future__ import annotations

import tomllib
from pathlib import Path

_REQUIRED_KEYS = {
    "ingestion": ["seasons", "rate_limit_delay_seconds", "max_retries", "batch_size"],
}

_DEFAULT_CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "config.toml"


class ConfigurationError(ValueError):
    pass


class IngestConfig:
    def __init__(self, data: dict) -> None:
        self._data = data

    @property
    def seasons(self) -> list[str]:
        return self._data["ingestion"]["seasons"]

    @property
    def rate_limit_delay_seconds(self) -> float:
        return float(self._data["ingestion"]["rate_limit_delay_seconds"])

    @property
    def max_retries(self) -> int:
        return int(self._data["ingestion"]["max_retries"])

    @property
    def batch_size(self) -> int:
        return int(self._data["ingestion"]["batch_size"])


def load_config(path: Path | None = None) -> IngestConfig:
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

    return IngestConfig(data)
