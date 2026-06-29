from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class Embedder(Protocol):
    """Turns text into fixed-dimension vectors. Implementations are swappable
    (an env-configured OpenAI-compatible backend in production; an in-memory
    fake in tests)."""

    model: str
    dimension: int

    def embed(self, texts: list[str]) -> list[list[float]]: ...
