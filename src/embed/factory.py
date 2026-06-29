from __future__ import annotations

from appconfig.settings import settings
from embed.openai_compatible import OpenAICompatibleEmbedder
from embed.protocol import Embedder


def get_embedder() -> Embedder:
    """Construct the configured embedder. Endpoint/key come from env; model and
    dimension from config/embedding.toml."""
    return OpenAICompatibleEmbedder(settings.embedding)
