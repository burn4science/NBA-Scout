from __future__ import annotations

from pydantic import BaseModel

# Typed tunable sections. These are populated from the TOML files under config/
# by the central Settings loader; each maps to one [section] table.


class IngestionConfig(BaseModel):
    """NBA data-ingestion tunables (config/ingestion.toml -> [ingestion])."""

    seasons: list[str]
    rate_limit_delay_seconds: float
    max_retries: int
    batch_size: int


class ChunkingConfig(BaseModel):
    """Document chunking tunables (config/embedding.toml -> [chunking])."""

    max_tokens: int
    overlap_tokens: int
    tokenizer: str
    merge_peers: bool = True


class EmbeddingConfig(BaseModel):
    """Embedding model identity and request shaping (config/embedding.toml -> [embedding])."""

    model: str
    dimension: int
    timeout_seconds: float
    batch_size: int
