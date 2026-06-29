> Note: the chunking package is `src/chunking/` (not `src/chunk/`) — `chunk`
> collides with Python's stdlib `chunk` module and gets shadowed on import.

## 1. Dependencies & Scaffolding

- [x] 1.1 Declare deps in `pyproject.toml`: `pgvector` + `openai` in base; `docling` under `[project.optional-dependencies].chunking` (heavy, image-only); update `uv.lock`
- [x] 1.2 Create module directories: `src/chunking/`, `src/embed/` (with `__init__.py`)
- [x] 1.3 Create `src/chunking/config.toml` (`max_tokens`, `overlap_tokens`, tokenizer/model knobs) and `src/embed/config.toml` (`model`, `dimension`, request timeout/batch size — no provider/endpoint, those are env)
- [x] 1.4 Extend `.env.example`: `APP_DB_PASSWORD`, `DATABASE_URL`/`MIGRATION_DATABASE_URL`/`APP_DATABASE_URL`, `EMBEDDING_BASE_URL`, `EMBEDDING_API_KEY`

## 2. Schema — ORM Models

- [x] 2.1 In `src/db/models.py`, add a `Scope` enum (`global`, `tenant`) and `SourceType` enum (`bio`, `scouting_note`, `draft_eval`) — as `enum.StrEnum`
- [x] 2.2 Add the `Document` model: `document_id` (UUID PK), `player_id` (FK→players, nullable), `scope`, `owner_tenant_id` (FK→tenants, nullable), `source_type`, `title`, `raw_text`, `created_at`, `updated_at`; with the scope/owner `CHECK` constraint
- [x] 2.3 Add the `Chunk` model: `chunk_id` (UUID PK), `document_id` (FK→documents, ON DELETE CASCADE), denormalized `player_id`/`scope`/`owner_tenant_id`, `chunk_index`, `content`, `metadata` (JSONB, attr aliased to `chunk_metadata`), `embedding` (`Vector(768)`), `embedding_model`, `embedding_dim`, `created_at`

## 3. Schema — Migration (tables, index, RLS, role)

- [x] 3.1 Author the migration (hand-written rather than autogenerate — enums, CHECK, Vector, RLS, and role don't autogenerate cleanly)
- [x] 3.2 Create the `documents` and `chunks` tables with the `CHECK` constraint
- [x] 3.3 Add the HNSW index on `chunks.embedding` (cosine ops) and btree indexes on `chunks.player_id` and `chunks(scope, owner_tenant_id)`
- [x] 3.4 Create the `nba_app` role (LOGIN, password from `APP_DB_PASSWORD`), grant DML on `documents`/`chunks` + SELECT on referenced tables; **not** the table owner
- [x] 3.5 `ENABLE` + `FORCE ROW LEVEL SECURITY` on `documents` and `chunks`; create the `tenant_isolation` policy using `NULLIF(current_setting('app.current_tenant', true), '')::uuid` (fail-closed on the empty-string GUC reset value)
- [x] 3.6 Implement `downgrade()`: drop policies, tables, indexes, role, and enum types cleanly
- [x] 3.7 Verified `uv run alembic upgrade head` then `downgrade -1` round-trips on the live DB

## 4. Database Session Module (tenant context injection)

- [x] 4.1 In `src/db/__init__.py`, create `get_app_engine()` (from `APP_DATABASE_URL`) and `get_admin_engine()` (from `MIGRATION_DATABASE_URL`)
- [x] 4.2 Implement `tenant_session(tenant_id)` context manager: transaction + `set_config('app.current_tenant', :tid, true)` (parameterizable, injection-safe form of `SET LOCAL`)
- [x] 4.3 Implement `admin_session()` context manager: transaction with no tenant set (global scope)
- [x] 4.4 Verified `tenant_session` injects the tenant (`test_set_config_injects_tenant` asserts `current_setting` == the UUID)

## 5. Chunking Module (Docling behind a protocol)

- [x] 5.1 Create `src/chunking/protocol.py`: a `Chunker` `Protocol` + a `Chunk` dataclass (`content`, `chunk_index`, `metadata`)
- [x] 5.2 Create `src/chunking/config.py` (mirrors `src/ingest/config.py`: `tomllib` + required-key validation + `ConfigurationError`)
- [x] 5.3 Create `src/chunking/docling_chunker.py`: `DoclingChunker` via Docling's HybridChunker (lazy imports so the module loads without the heavy stack)
- [x] 5.4 Create `src/chunking/factory.py`: build the configured `Chunker`
- [x] 5.5 `DoclingChunker` test (`test_docling_chunker.py`, `importorskip("docling")` — runs in the image/CI)

## 6. Embedding Module (env-configured OpenAI-compatible endpoint)

- [x] 6.1 Create `src/embed/protocol.py`: an `Embedder` `Protocol` with `embed(...)`, `model`, `dimension`
- [x] 6.2 Create `src/embed/config.py` (validation + `ConfigurationError`; `model`, `dimension`, `timeout_seconds`, `batch_size`)
- [x] 6.3 Create `src/embed/openai_compatible.py`: an `Embedder` using the `openai` client against `EMBEDDING_BASE_URL`/`EMBEDDING_API_KEY` from env; asserts vector length == configured `dimension`
- [x] 6.4 Create `src/embed/factory.py`: read endpoint/key from env + model/dim from config
- [x] 6.5 `InMemoryEmbedder` (deterministic fake) for tests; dimension-mismatch + missing-base-url tests pass

## 7. Pipeline Orchestrator + Placeholder Seed

- [x] 7.1 Create `src/embed/seed.py`: placeholder `global` bios + one `tenant` scouting note for each of two seed tenants
- [x] 7.2 Create `src/embed/pipeline.py`: document → `Chunker` → `Embedder` → `chunks` with denormalized scope fields + provenance; global via `admin_session`, tenant via `tenant_session`; loguru summary
- [x] 7.3 Confirmed end-to-end via `docker compose run --rm embed` (Docling chunked, 4 docs / 4 chunks, INFO summary clean)
- [x] 7.4 Verified live against the DB with LM Studio (`embeddinggemma-300m`): real `chunks` rows have non-null 768-dim `embedding`, `embedding_dim = 768`, `embedding_model = text-embedding-embeddinggemma-300m`, scope set; zero null/wrong-dim rows

## 8. Isolation Verification & Tests

- [x] 8.1 Integration test (the key proof): under `tenant_session(A)` a filter-less select over `chunks` returns global + A only; under `tenant_session(B)` none of A's private rows; no context → global only
- [x] 8.2 Integration test: counting another tenant's private chunk under tenant A returns zero (RLS, not app filtering)
- [x] 8.3 `FORCE` verified: `pg_class.relforcerowsecurity = true`; owner is `nba_user`, policy applies to it; `admin_session` (owner) is default-denied to global rows
- [x] 8.4 Unit tests: config validation raises `ConfigurationError` on missing keys for `src/chunking` and `src/embed`
- [x] 8.5 `uv run ruff check src/ tests/` and `ruff format --check` pass

## Result

37/37 tasks complete. **26 passed, 1 skipped** locally (Docling, runs in image);
live `docker compose run --rm embed` produced real 768-dim `embeddinggemma-300m`
vectors across both visibility classes with zero null/wrong-dim rows.

Known limitation (out of MVP scope): the seed pipeline is additive, not idempotent
— re-running inserts duplicate documents. Real-content ingestion later should
upsert or guard on a natural key (mirrors the Phase 1 ingest pattern).
