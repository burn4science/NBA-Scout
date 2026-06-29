## Why

Phase 1 established the global relational layer. The platform's actual value, however, lives in the **hybrid loop**: SQL pre-filtering hands a set of permitted player IDs to a constrained vector search over text, fusing structured metrics with unstructured scouting prose. None of that text/embedding layer exists yet — only the `pgvector` extension is enabled.

This change builds the **pipeline shape** for that layer end to end, with placeholder content, so real bios and scouting notes can be filled in later without touching the structure or the security contract. The two expensive-to-change concerns are designed in correctly from the start: **multi-tenant isolation enforced by the database** (Row-Level Security, not application code), and a **swappable Docling chunker + embedder** so neither tool is hard-wired.

Scope is MVP: a credible proof that the necessary mechanisms are in place — not a production-hardened deployment.

## What Changes

- New schema: `documents` (source unit) and `chunks` (embed + retrieval unit) with an explicit `scope` enum (`global` vs `tenant`), denormalized tenant fields on `chunks` for a join-free retrieval path, a `vector(768)` embedding column with an HNSW index, and `embedding_model`/`embedding_dim` provenance columns
- **Row-Level Security** on `documents` and `chunks`: `ENABLE` + `FORCE`, a `tenant_isolation` policy keyed on `current_setting('app.current_tenant')`, and a dedicated **non-owner least-privilege app role** so the application physically cannot bypass the policy
- New `src/db/__init__.py` session module providing tenant-scoped (`SET LOCAL app.current_tenant`) and admin (global-scope) sessions
- New `src/chunking/` module: a `Chunker` protocol with a Docling implementation (swappable)
- New `src/embed/` module: an `Embedder` protocol with a single OpenAI-compatible client targeting LM Studio (local default) or Ollama Cloud, both serving `embeddinggemma-300m` (768-dim, interchangeable vectors)
- New `src/embed/pipeline.py` orchestrator: placeholder docs → `Document` rows → Docling chunks → embeddings → `chunks` rows, writing global content via an admin session and tenant content via tenant-scoped sessions
- Per-module private `config.toml` for chunking and embedding; `.env.example` gains `APP_DATABASE_URL`, `MIGRATION_DATABASE_URL`, embedding base URLs, and `OLLAMA_API_KEY`

## Capabilities

### New Capabilities

- `embedding-pipeline`: Docling chunking and embedding generation (LM Studio / Ollama Cloud, `embeddinggemma-300m`) behind swappable protocols, writing scope-tagged `chunks` with embedding provenance from placeholder content
- `tenant-isolation`: database-enforced multi-tenant isolation — a non-owner app role under `FORCE` RLS, dynamic per-transaction tenant context injection, and a fail-closed default-deny posture for private rows

### Modified Capabilities

- `database-schema`: adds the `documents` and `chunks` tables, the HNSW vector index, the RLS policies, and the dedicated app role

## Impact

- **New dependencies**: `docling`, `pgvector` (SQLAlchemy `Vector` type), `openai` (OpenAI-compatible embeddings client)
- **New top-level directories**: `src/chunking/`, `src/embed/`
- **Modified**: `src/db/__init__.py` (was empty → session module), `src/db/models.py` (new ORM models), `docker-compose.yml` (app-role bootstrap), `.env.example`
- **Schema**: additive Alembic migration on top of `a1b2c3d4e5f6`; reversible
- **No existing Phase 1 code is modified** beyond the additive items above
