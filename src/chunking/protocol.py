from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable


@dataclass
class Chunk:
    """One retrievable unit produced from a document's raw text."""

    content: str
    chunk_index: int
    metadata: dict = field(default_factory=dict)


@runtime_checkable
class Chunker(Protocol):
    """Splits raw text into ordered chunks. Implementations are swappable
    (Docling today) without touching the pipeline."""

    def chunk(self, raw_text: str, metadata: dict) -> list[Chunk]: ...
