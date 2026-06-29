from __future__ import annotations

import io

from chunking.config import ChunkConfig, load_config
from chunking.protocol import Chunk


class DoclingChunker:
    """Layout-aware chunking via Docling's HybridChunker.

    Docling imports are deferred to construction time so this module remains
    importable in the light local test venv (where `docling` is not installed);
    the heavy stack is only required to actually instantiate the chunker.
    """

    def __init__(self, config: ChunkConfig | None = None) -> None:
        self._config = config or load_config()
        from docling.chunking import HybridChunker

        self._chunker = HybridChunker(
            tokenizer=self._config.tokenizer,
            max_tokens=self._config.max_tokens,
            merge_peers=self._config.merge_peers,
        )

    def chunk(self, raw_text: str, metadata: dict) -> list[Chunk]:
        from docling.datamodel.document import DocumentStream
        from docling.document_converter import DocumentConverter

        stream = DocumentStream(name="placeholder.md", stream=io.BytesIO(raw_text.encode("utf-8")))
        doc = DocumentConverter().convert(stream).document

        chunks: list[Chunk] = []
        for index, dl_chunk in enumerate(self._chunker.chunk(dl_doc=doc)):
            headings = list(getattr(dl_chunk.meta, "headings", None) or [])
            chunks.append(
                Chunk(
                    content=dl_chunk.text,
                    chunk_index=index,
                    metadata={**metadata, "headings": headings},
                )
            )
        return chunks
