from __future__ import annotations

from appconfig.settings import settings
from chunking.docling_chunker import DoclingChunker
from chunking.protocol import Chunker


def get_chunker() -> Chunker:
    """Construct the configured chunker. Swap this single function to change
    the chunking backend."""
    return DoclingChunker(settings.chunking)
