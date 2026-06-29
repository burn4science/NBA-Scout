## 1. Dependency & scaffolding

- [x] 1.1 Add `pydantic-settings` to `pyproject.toml` via `uv add pydantic-settings`
- [x] 1.2 Create the `src/config/` package (`__init__.py`) and decide the import name (`config`, fall back to `appconfig` if it clashes with the repo-root `config/` data folder)

## 2. Relocate config files (grouped by pipeline stage)

- [x] 2.1 Create `config/ingestion.toml` with the `[ingestion]` section, moving the values from `config/config.toml` verbatim
- [x] 2.2 Create `config/embedding.toml` with the `[chunking]` section (from `src/chunking/config.toml`) and the `[embedding]` section (from `src/embed/config.toml`), preserving comments
- [x] 2.3 Verify no `config.toml` remains under `src/` after relocation

## 3. Central loader & typed settings

- [x] 3.1 Define nested Pydantic models: `IngestionConfig`, `ChunkingConfig`, `EmbeddingConfig` matching current keys/types
- [x] 3.2 Define a `Secrets`/env model with distinct typed fields for `DATABASE_URL`, `MIGRATION_DATABASE_URL`, `APP_DATABASE_URL`, `EMBEDDING_BASE_URL`, `EMBEDDING_API_KEY`, `HOST_SHARED_DATA_DIR`
- [x] 3.3 Build the `BaseSettings` root with `settings_customise_sources` wiring `TomlConfigSettingsSource` for both `config/ingestion.toml` and `config/embedding.toml` plus env/`.env`
- [x] 3.4 Expose a module-level `settings` instance loaded once at import; load `.env` centrally here
- [x] 3.5 Add a loguru log line on successful load (no secret values logged)

## 4. Validation & dimension guard

- [x] 4.1 Ensure required-field validation raises a clear error naming any missing/malformed TOML key or secret
- [x] 4.2 Add a startup assertion that `settings.embedding.dimension == EMBEDDING_DIM` (imported from `src/db/models.py`), failing loudly with an explanatory message

## 5. Repoint consumers

- [x] 5.1 `src/chunking/docling_chunker.py` and `src/chunking/factory.py` → read `settings.chunking` (keep optional-override seam for tests)
- [x] 5.2 `src/embed/openai_compatible.py` → read `settings.embedding` and the embedding endpoint/key from `settings`; remove direct `os.environ` reads
- [x] 5.3 `src/embed/factory.py` and `src/embed/pipeline.py` → read `settings.embedding`; remove the `load_dotenv()` call in `pipeline.py`
- [x] 5.4 `src/ingest/run.py` → read `settings.ingestion` and DB URL from `settings`; remove its `load_dotenv()` call

## 6. Remove old machinery

- [x] 6.1 Delete `src/chunking/config.py`, `src/chunking/config.toml`, `src/embed/config.py`, `src/embed/config.toml`, `src/ingest/config.py`, and `config/config.toml`
- [x] 6.2 Grep for stale references to `load_config`, `ConfigurationError`, and the deleted paths; remove or repoint

## 7. Tests, lint, verify

- [x] 7.1 Update tests that passed explicit config paths to use `settings` sub-models or fixture TOML; preserve factory override seams
- [x] 7.2 Update `.env.example` comments that point at `src/embed/config.toml` to reference `config/embedding.toml`
- [x] 7.3 Run `ruff check` + `ruff format`
- [x] 7.4 Run the full test suite and confirm green; manually confirm app startup loads `settings` and the dimension assertion passes
