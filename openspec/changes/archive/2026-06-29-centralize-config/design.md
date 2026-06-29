## Context

Configuration today is split three ways with copy-pasted machinery:

- `config/config.toml` (`[ingestion]`) read by `src/ingest/config.py` (reaches up `../../config/`).
- `src/chunking/config.toml` (`[chunking]`) read by `src/chunking/config.py` (local sibling).
- `src/embed/config.toml` (`[embedding]`) read by `src/embed/config.py` (local sibling).

Each loader is a near-identical `load_config()` + `ConfigurationError` + required-keys validation loop differing only in section/key names. Secrets are read ad-hoc through `os.environ` in `src/embed/openai_compatible.py` and `src/ingest/run.py`, with `load_dotenv()` called separately in `src/ingest/run.py` and `src/embed/pipeline.py`. The embedding `dimension` (768) is duplicated across `config.toml`, `src/db/models.py`, `src/embed/in_memory.py`, and a frozen Alembic migration.

The user wants one `config/` folder organized for the configurer (not the code), and one central loader that reads everything at startup so code just reads from an in-memory object.

## Goals / Non-Goals

**Goals:**
- One `config/` folder, grouped by pipeline stage (`ingestion.toml`, `embedding.toml`).
- One central `src/config/` package exposing a single typed `settings` object loaded once at startup.
- Unify TOML tunables and `.env` secrets behind `settings`, with secrets as explicit typed fields.
- Replace the three hand-rolled loaders with `pydantic-settings`.
- Fail-loud validation, including an embedding-dimension drift assertion.

**Non-Goals:**
- Changing any `.env` variable names or the `.env` contract.
- Changing the database schema or touching the frozen Alembic migration.
- Moving `EMBEDDING_DIM` out of `src/db/models.py` (it is needed at import time to declare `Vector(N)`).
- Altering ingestion/embedding behavior beyond where they obtain config.

## Decisions

**1. `pydantic-settings` with `TomlConfigSettingsSource` over hand-rolled loaders.**
A `BaseSettings` subclass with nested models (`IngestionConfig`, `ChunkingConfig`, `EmbeddingConfig`) gives typed validation, clear errors, and TOML+`.env` unification for free. Customize `settings_customise_sources` to add both `config/ingestion.toml` and `config/embedding.toml` as TOML sources alongside env/`.env`. Rejected: keeping the hand-rolled loaders (three copies to maintain, no typing); Dynaconf (heavier, less typed).

**2. Group TOML by pipeline stage, not module.**
`config/ingestion.toml` → `[ingestion]`; `config/embedding.toml` → `[chunking]` + `[embedding]`. This intentionally overrides the standing "config private to each module" convention per explicit user instruction — the organizing axis is the configurer's mental model. The central loader makes file layout independent of code, so grouping is purely a human-ergonomics choice.

**3. One `settings` object holds tunables AND secrets, secrets as distinct fields.**
Tunables come from TOML; secrets (`DATABASE_URL`, `MIGRATION_DATABASE_URL`, `APP_DATABASE_URL`, `EMBEDDING_BASE_URL`, `EMBEDDING_API_KEY`, `HOST_SHARED_DATA_DIR`) come from env/`.env`. Keeping secrets as named typed fields (not a dict) keeps their reach explicit and greppable. `.env` is loaded once by the package; scattered `load_dotenv()` calls are removed.

**4. Guard the dimension coupling instead of moving it.**
`src/db/models.py` keeps `EMBEDDING_DIM = 768` because SQLAlchemy needs it at import time. Add a startup assertion `settings.embedding.dimension == EMBEDDING_DIM` so any divergence fails loudly. The Alembic migration constant is frozen history and left untouched.

**5. Import surface.**
Expose a module-level `settings` (e.g. `from config import settings`). Consumers (`docling_chunker.py`, both `factory.py`, `openai_compatible.py`, `pipeline.py`, `run.py`) drop their `load_config()` / `os.environ` calls and read `settings.*`. Factories that took an injected config keep that seam for tests by accepting an optional override, defaulting to the relevant `settings` sub-model.

## Risks / Trade-offs

- **Secrets reachable app-wide via `settings`** → Keep them as distinct typed fields (not a catch-all dict) so usage is explicit and auditable; never log the `settings` object wholesale.
- **`src/config/` package name could shadow the top-level `config/` folder or stdlib expectations** → Package lives under `src/` (import name `config`); the data folder is the repo-root `config/`. Confirm `src` layout / `PYTHONPATH` keeps these distinct; if collision risk, name the import `appconfig`.
- **New dependency** → `pydantic-settings` is small, widely used, and aligns with the project's Pydantic/FastAPI stack.
- **Dimension assertion runs at startup, not import** → Acceptable; `models.py` import-time constant remains the schema source of truth, assertion catches config drift early in app boot.
- **Tests that passed explicit config paths** → Replace with constructing sub-model instances or pointing `pydantic-settings` at fixture TOML; preserve the optional-override seam in factories.

## Migration Plan

1. Add `pydantic-settings` via `uv`.
2. Create `src/config/` with nested typed models + `settings`, sourcing both TOML files and `.env`.
3. Create `config/ingestion.toml` and `config/embedding.toml`; move existing values verbatim.
4. Repoint all consumers to `settings`; remove `load_dotenv()` call sites.
5. Add the dimension drift assertion.
6. Delete the six old config files.
7. Run ruff + the test suite; fix any path-based test fixtures.

Rollback: revert the commit; old per-module files and loaders are restored together.

## Open Questions

- Import name: `config` vs `appconfig` to avoid any clash with the data folder — resolve during implementation by checking the `src` package layout.
- Whether `settings` should be a true singleton (module-level instance) vs. a cached factory (`@lru_cache`) for test override ergonomics — lean module-level instance with factory seams on consumers.
