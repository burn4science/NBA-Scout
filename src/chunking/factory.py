from __future__ import annotations

from chunking.config import load_config
from chunking.docling_chunker import DoclingChunker
from chunking.protocol import Chunker


def get_chunker() -> Chunker:
    """Construct the configured chunker. Swap this single function to change
    the chunking backend."""
    return DoclingChunker(load_config())
