"""DoclingChunker test. Skips when the heavy `docling` stack is absent (the
light local venv); runs in the image/CI where the `chunking` extra is installed.
"""

import pytest

pytest.importorskip("docling")

from chunking.docling_chunker import DoclingChunker  # noqa: E402
from chunking.protocol import Chunk  # noqa: E402

_SAMPLE = (
    "# Scouting Report\n\n"
    "Player shows elite first-step quickness and strong help-side instincts. "
    "Projects as a switchable perimeter defender with developing pull-up range.\n\n"
    "## Weaknesses\n\n"
    "Inconsistent free-throw mechanics and occasional over-helping off the weak side."
)


def test_produces_ordered_chunks() -> None:
    chunks = DoclingChunker().chunk(_SAMPLE, {"document_title": "sample"})
    assert len(chunks) >= 1
    assert all(isinstance(c, Chunk) for c in chunks)
    assert [c.chunk_index for c in chunks] == list(range(len(chunks)))
    assert all(c.content.strip() for c in chunks)
    assert all(c.metadata.get("document_title") == "sample" for c in chunks)
