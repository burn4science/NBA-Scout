from __future__ import annotations

import hashlib


class InMemoryEmbedder:
    """Deterministic, dependency-free embedder for tests. Maps text to a stable
    pseudo-vector so isolation/pipeline tests need no live backend."""

    def __init__(self, model: str = "in-memory", dimension: int = 768) -> None:
        self.model = model
        self.dimension = dimension

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._vector(text) for text in texts]

    def _vector(self, text: str) -> list[float]:
        values: list[float] = []
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        while len(values) < self.dimension:
            digest = hashlib.sha256(digest).digest()
            values.extend(byte / 255.0 for byte in digest)
        return values[: self.dimension]
