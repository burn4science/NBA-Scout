from __future__ import annotations

from embed.config import load_config
from embed.openai_compatible import OpenAICompatibleEmbedder
from embed.protocol import Embedder


def get_embedder() -> Embedder:
    """Construct the configured embedder. Endpoint/key come from env; model and
    dimension from config.toml."""
    return OpenAICompatibleEmbedder(load_config())
