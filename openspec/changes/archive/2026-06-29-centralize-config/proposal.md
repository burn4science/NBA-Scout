## Why

Configuration is scattered across the codebase: tunables live in `config/config.toml` plus per-module `src/chunking/config.toml` and `src/embed/config.toml`, each loaded by a near-identical hand-rolled `config.py` (three copies of the same `load_config`/`ConfigurationError`/validation loop), while secrets are read ad-hoc via `os.environ` and repeated `load_dotenv()` calls. A configurer must know the code's module layout to find what to tune, and there is no single source of truth loaded once at startup. This change consolidates all configuration into one `config/` folder organized for the human configurer, behind one central typed `settings` object.

## What Changes

- **NEW** central configuration package `src/config/` that loads all config once at startup and exposes a single typed `settings` object; code reads attributes (e.g. `settings.embedding.model`, `settings.ingestion.seasons`) and never references a config file path again.
- TOML is grouped by **pipeline stage** for the configurer's mental model — not by code module — into two files: `config/ingestion.toml` (`[ingestion]`) and `config/embedding.toml` (`[chunking]` + `[embedding]`).
- The `settings` object unifies **TOML tunables and `.env`-derived values** (database URLs, embedding endpoint/key, shared data dir), with secrets kept as distinct typed fields so their reach stays explicit.
- Adopt **`pydantic-settings`** (new dependency) using `BaseSettings` + `TomlConfigSettingsSource`, replacing the three hand-rolled loaders entirely.
- A startup assertion verifies `settings.embedding.dimension == EMBEDDING_DIM` (the import-time schema constant in `src/db/models.py`) so any drift fails loudly.
- **BREAKING (internal)**: removes `src/chunking/config.py`, `src/chunking/config.toml`, `src/embed/config.py`, `src/embed/config.toml`, `src/ingest/config.py`, and `config/config.toml`; all config consumers switch to importing from the new package. Scattered `load_dotenv()` calls are consolidated into the central loader.

## Capabilities

### New Capabilities
- `configuration`: Centralized, typed application configuration — a single `config/` folder grouped by pipeline stage and one startup-loaded `settings` object that unifies TOML tunables and `.env` secrets, with fail-loud validation.

### Modified Capabilities
<!-- No spec-level requirement changes to data-ingestion or embedding-pipeline; only how they obtain config (implementation detail). -->

## Impact

- **New dependency**: `pydantic-settings` (added via `uv` to `pyproject.toml`).
- **New code**: `src/config/` package (loader + typed models).
- **Removed**: `config/config.toml`, `src/chunking/config.{py,toml}`, `src/embed/config.{py,toml}`, `src/ingest/config.py`.
- **New config files**: `config/ingestion.toml`, `config/embedding.toml`.
- **Updated consumers**: `src/chunking/docling_chunker.py`, `src/chunking/factory.py`, `src/embed/openai_compatible.py`, `src/embed/factory.py`, `src/embed/pipeline.py`, `src/ingest/run.py`.
- **Coupling guarded, not moved**: `EMBEDDING_DIM` stays in `src/db/models.py` (needed at import time for `Vector(N)`); the frozen Alembic migration constant is untouched.
- **`.env` contract unchanged**: same variable names; only the loading mechanism is centralized.
