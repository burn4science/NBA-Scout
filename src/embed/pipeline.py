"""Embedding pipeline: placeholder documents -> chunks with embeddings.

Global documents are written through an admin (owner) session; tenant documents
through a tenant-scoped session so RLS stamps and isolates them. `run_pipeline`
takes the chunker and embedder as arguments so it can be driven with in-memory
fakes in tests; `main` wires the real Docling chunker and the configured embedder.
"""

from __future__ import annotations

import uuid

from sqlalchemy import Connection, insert, select

from chunking.factory import get_chunker
from chunking.protocol import Chunker
from db import admin_session, tenant_session
from db.models import Chunk, Document, Tenant
from embed.factory import get_embedder
from embed.logger import get_logger
from embed.protocol import Embedder
from embed.seed import GLOBAL_DOCUMENTS, SEED_TENANTS, TENANT_DOCUMENTS, SeedDocument


def ensure_tenants(names: tuple[str, ...]) -> dict[str, uuid.UUID]:
    """Create the named tenants if absent; return name -> tenant_id."""
    mapping: dict[str, uuid.UUID] = {}
    with admin_session() as conn:
        for name in names:
            tenant_id = conn.execute(
                select(Tenant.tenant_id).where(Tenant.name == name)
            ).scalar_one_or_none()
            if tenant_id is None:
                tenant_id = conn.execute(
                    insert(Tenant).values(name=name).returning(Tenant.tenant_id)
                ).scalar_one()
            mapping[name] = tenant_id
    return mapping


def _write_document(
    conn: Connection,
    chunker: Chunker,
    embedder: Embedder,
    doc: SeedDocument,
    owner_tenant_id: uuid.UUID | None,
) -> int:
    """Insert one document and its embedded chunks; return the chunk count."""
    document_id = conn.execute(
        insert(Document)
        .values(
            player_id=doc.player_id,
            scope=doc.scope,
            owner_tenant_id=owner_tenant_id,
            source_type=doc.source_type,
            title=doc.title,
            raw_text=doc.raw_text,
        )
        .returning(Document.document_id)
    ).scalar_one()

    pieces = chunker.chunk(doc.raw_text, {"document_title": doc.title})
    vectors = embedder.embed([piece.content for piece in pieces])

    rows = [
        {
            "document_id": document_id,
            "player_id": doc.player_id,
            "scope": doc.scope,
            "owner_tenant_id": owner_tenant_id,
            "chunk_index": piece.chunk_index,
            "content": piece.content,
            "chunk_metadata": piece.metadata,
            "embedding": vector,
            "embedding_model": embedder.model,
            "embedding_dim": embedder.dimension,
        }
        for piece, vector in zip(pieces, vectors, strict=True)
    ]
    if rows:
        conn.execute(insert(Chunk), rows)
    return len(rows)


def run_pipeline(chunker: Chunker, embedder: Embedder, log) -> tuple[int, int]:
    """Seed both visibility classes. Returns (documents, chunks) written."""
    tenants = ensure_tenants(SEED_TENANTS)
    log.info(f"Seed tenants ready: {list(tenants)}")

    documents = 0
    chunks = 0

    for doc in GLOBAL_DOCUMENTS:
        with admin_session() as conn:
            n = _write_document(conn, chunker, embedder, doc, None)
        documents += 1
        chunks += n
        log.info(f"global: '{doc.title}' -> {n} chunks")

    for doc in TENANT_DOCUMENTS:
        tenant_id = tenants[doc.owner_tenant_name]
        with tenant_session(tenant_id) as conn:
            n = _write_document(conn, chunker, embedder, doc, tenant_id)
        documents += 1
        chunks += n
        log.info(f"tenant[{doc.owner_tenant_name}]: '{doc.title}' -> {n} chunks")

    log.info(f"Pipeline complete. Documents: {documents}, chunks: {chunks}")
    return documents, chunks


def main() -> None:
    from dotenv import load_dotenv

    load_dotenv()
    log = get_logger()
    log.info("NBA Scout embedding pipeline starting")
    run_pipeline(get_chunker(), get_embedder(), log)


if __name__ == "__main__":
    main()
