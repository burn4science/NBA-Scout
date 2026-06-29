from __future__ import annotations

import os

from embed.config import EmbedConfig, load_config


class EmbeddingError(RuntimeError):
    pass


class OpenAICompatibleEmbedder:
    """Embedder backed by any OpenAI-compatible `/v1/embeddings` endpoint
    (LM Studio locally, Ollama Cloud on the homelab). The endpoint and key come
    from the environment, so the same image runs anywhere without rebuild."""

    def __init__(
        self,
        config: EmbedConfig | None = None,
        base_url: str | None = None,
        api_key: str | None = None,
    ) -> None:
        self._config = config or load_config()
        self.model = self._config.model
        self.dimension = self._config.dimension

        base_url = base_url or os.environ.get("EMBEDDING_BASE_URL")
        if not base_url:
            raise EmbeddingError(
                "EMBEDDING_BASE_URL is not set. Configure it in .env "
                "(e.g. http://localhost:1234/v1 for LM Studio)."
            )
        api_key = api_key or os.environ.get("EMBEDDING_API_KEY") or "not-needed"

        from openai import OpenAI

        self._client = OpenAI(
            base_url=base_url, api_key=api_key, timeout=self._config.timeout_seconds
        )

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        vectors: list[list[float]] = []
        for start in range(0, len(texts), self._config.batch_size):
            batch = texts[start : start + self._config.batch_size]
            response = self._client.embeddings.create(model=self.model, input=batch)
            for item in response.data:
                vector = list(item.embedding)
                if len(vector) != self.dimension:
                    raise EmbeddingError(
                        f"Backend returned {len(vector)}-dim vector; "
                        f"config expects {self.dimension}. Check the model/dimension."
                    )
                vectors.append(vector)
        return vectors
