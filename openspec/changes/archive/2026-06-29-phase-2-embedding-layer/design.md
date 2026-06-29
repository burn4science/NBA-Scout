## Context

Phase 1 left a clean relational spine and an enabled `pgvector` extension. This change adds the unstructured/embedding layer. Two design forces dominate and were settled with the project owner during exploration:

1. **Isolation must be enforced by the database, not the application.** The blueprint's thesis is "secure multi-tenant filtering on a shared physical database using dynamic context injection." A `WHERE` clause in application code proves nothing and a buggy or prompt-injected query (a real risk per Phase 3) would leak. Row-Level Security with a non-owner app role makes isolation hold regardless of query correctness.
2. **Infrastructure tools must be replaceable.** Docling (chunking) and the embedding backend sit behind narrow protocols so they can be swapped without touching the pipeline or schema.

This is an MVP proof, not a production system. We deliberately stop short of production hardening (see Non-Goals).

## Goals / Non-Goals

**Goals:**
- `documents` / `chunks` schema with an explicit `scope` enum and embedding provenance
- HNSW index on a `vector(768)` column (EmbeddingGemma's native dimension)
- Database-enforced isolation: `FORCE` RLS + a dedicated non-owner app role + `SET LOCAL` tenant context + default-deny
- Docling chunking behind a `Chunker` protocol; embedding behind an `Embedder` protocol
- A runnable pipeline that populates `chunks` from placeholder content, demonstrating both visibility classes
- Follow project conventions: `uv`, `loguru`, `ruff`, per-module private `config.toml`, `.env`, Alembic

**Non-Goals:**
- Real bios / scouting-note content (placeholder only; content filled later)
- The SQL→vector retrieval tool layer and LangGraph orchestration (Phase 3)
- LiteLLM proxy, token-quota middleware, Langfuse (Phase 4)
- Cross-encoder re-ranking, eval suite (Phase 5)
- Production hardening: per-tenant encryption-at-rest, audit logging, pgbouncer transaction-pooling `SET` semantics, secret-manager integration
- Embedding provider abstraction beyond LM Studio + Ollama Cloud (explicitly out of scope per owner)

## Decisions

### D1 — Two tables: `documents` (source) → `chunks` (retrieval unit)

`documents` holds the raw source text and its ownership; `chunks` holds the embeddable/retrievable units. `player_id`, `scope`, and `owner_tenant_id` are **denormalized onto `chunks`** so the retrieval hot path (`vector search WHERE player_id = ANY(:ids) AND visible`) needs no join to `documents`.

**Alternative considered:** a single wide table. Rejected — conflates the editable source with immutable derived vectors and forces re-chunking semantics into the same row.

### D2 — Explicit `scope` enum, never NULL-encoded tenancy

`scope` is an enum (`global`, `tenant`) with a `CHECK` constraint: `(scope='global' AND owner_tenant_id IS NULL) OR (scope='tenant' AND owner_tenant_id IS NOT NULL)`. Global text (shared bios) is embedded once and visible to all tenants; tenant text (scouting notes) is owned by exactly one tenant.

**Alternative considered:** "NULL `tenant_id` means shared." Rejected — encoding "global" as NULL is the classic source of leaks (one forgotten `IS NULL` branch) and cannot be `CHECK`-constrained as cleanly.

### D3 — Isolation level: FORCE RLS + dedicated non-owner app role (L2 + L3 touches)

The load-bearing decision is **who the app connects as**: RLS automatically applies to any role that is neither the table owner nor a superuser. The app connects as a least-privilege `nba_app` role (DML only, not owner). `FORCE ROW LEVEL SECURITY` additionally subjects the owner/migration path to the policy, closing the "owner bypasses RLS" trap. The policy is:

```sql
USING (scope = 'global'
   OR owner_tenant_id = current_setting('app.current_tenant', true)::uuid)
```

The `true` second argument makes an unset setting return NULL rather than error, yielding **default-deny**: with no tenant context, only `global` rows are visible, never private ones.

**Alternatives considered:** (a) application-layer `WHERE` filtering only — rejected, proves nothing and fails under buggy/injected queries; (b) RLS while the app connects as table owner — rejected, the policy is silently bypassed (false security). See `tenant-isolation` spec for the guarantees these enable.

### D4 — Dynamic context injection via `SET LOCAL` in a session context manager

`src/db/__init__.py` exposes `tenant_session(tenant_id)` (opens a transaction, issues `SET LOCAL app.current_tenant = :tid`, so the setting is scoped to that transaction) and `admin_session()` (no tenant set → writes/reads global scope). `SET LOCAL` requires a transaction-scoped connection, which the existing `NullPool` setup already encourages.

**Alternative considered:** session-level `SET` on a pooled connection. Rejected — leaks tenant context across requests under pooling; `SET LOCAL` is fail-safe.

### D5 — Embedding: one OpenAI-compatible client, endpoint driven entirely by env

LM Studio (local dev) and Ollama Cloud (homelab/prod) both expose an OpenAI-compatible `/v1/embeddings` endpoint and both serve `embeddinggemma-300m`. Because the endpoint is the *only* thing that differs, the client takes `EMBEDDING_BASE_URL` + `EMBEDDING_API_KEY` from `.env` and there is **no provider branching** — the same image and the same `config.toml` run against either backend by changing env alone. This is what makes the container homelab-independent (Portainer pulls and runs with no reach-back to the dev host). `model` and `dimension` (stable, identity of the vector space) live in `src/embed/config.toml`; the endpoint and key (environment-specific) live in `.env`. Because the **same model** runs on both backends, vectors share one space — switching needs no re-embedding. Dimension is fixed at **768** (EmbeddingGemma native; Matryoshka truncation to 512/256/128 is a later option). `embedding_model`/`embedding_dim` provenance columns detect a stale vector if the model ever changes.

**Alternative considered:** a `provider` enum + factory selecting base_url/key per provider. Rejected — both backends are OpenAI-compatible, so the provider distinction collapses to a base URL; an env-driven endpoint is simpler and keeps the image environment-agnostic. **Also considered:** LiteLLM as the gateway now — deferred to Phase 4 (proxy + token tracking); two same-model OpenAI-compatible backends don't need it.

### D8 — Docling is an optional dependency; light local test venv

`docling` (which pulls `torch`) is declared under `[project.optional-dependencies].chunking`, not the base dependencies. The Docker image installs it (`uv sync --extra chunking`) so containers are self-contained; the local venv stays light for fast testing. The Docling chunker test uses `pytest.importorskip("docling")` so the suite passes locally without the heavy stack and exercises Docling in the image/CI.

### D6 — Docling and embedder behind narrow protocols

`Chunker.chunk(raw_text, metadata) -> list[Chunk]` and `Embedder.embed(texts) -> list[list[float]]` (plus `model`/`dimension`). Concrete implementations (`DoclingChunker`, the OpenAI-compatible embedder) are constructed by small factories from per-module `config.toml`. This keeps Docling/the backend swappable and lets the pipeline be unit-tested with in-memory fakes (no live LM Studio needed).

### D7 — Per-module private `config.toml`

`src/chunking/config.toml` and `src/embed/config.toml`, each loaded and validated by its module's `config.py` (mirroring `src/ingest/config.py`: `tomllib` + required-key check + `ConfigurationError`). Honors the project rule "config files are private to their module — no cross-module sharing." Secrets (Ollama API key) and environment-specific base URLs live in `.env`, never in TOML.

## Risks / Trade-offs

- **LM Studio must be running** for a live embedding run → the pipeline depends on a local service. Mitigation: protocol seam allows an in-memory fake embedder for tests; the live run is a manual verification step, not a unit test.
- **`SET LOCAL` + connection pooling** → safe today (NullPool, transaction-scoped). A future pgbouncer in transaction-pooling mode would need a `RESET`/`DISCARD` strategy. Noted as a Phase-4 ops concern, out of MVP scope.
- **Role bootstrap** → the `nba_app` role and its grants must exist before the app connects. Mitigation: create the role + grants inside the migration (or a documented bootstrap step in `docker-compose.yml`); document both URLs in `.env.example`.
- **Model drift invalidates vectors** → changing the embedding model changes the vector space. Mitigation: provenance columns make stale vectors detectable; an MVP re-embed is a full pipeline re-run.
- **HNSW build parameters** → defaults are fine for MVP volumes. Tuning `m`/`ef_construction` is deferred until real content exists.

## Migration Plan

1. `docker compose up -d db` — PostgreSQL with pgvector (from Phase 1)
2. `uv run alembic upgrade head` — applies the additive migration: tables, HNSW index, RLS policies, `nba_app` role
3. Configure `.env`: `MIGRATION_DATABASE_URL` (owner), `APP_DATABASE_URL` (`nba_app`), embedding base URLs, `OLLAMA_API_KEY`
4. Start LM Studio serving `embeddinggemma-300m`
5. `uv run python -m embed.pipeline` — seeds placeholder documents and populates `chunks`
6. Verify isolation (see tasks): tenant A sees global + A's chunks; tenant B sees none of A's private chunks; no context → global only
7. Rollback: `uv run alembic downgrade -1` drops the new objects and role cleanly
