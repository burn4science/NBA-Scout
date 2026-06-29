## ADDED Requirements

### Requirement: Single centralized configuration folder

The system SHALL keep all human-editable configuration under one top-level `config/` folder, organized by pipeline stage rather than by code module, so a configurer can locate and edit settings without knowledge of the source layout. No `config.toml` files SHALL reside inside `src/` modules.

#### Scenario: Config grouped by pipeline stage

- **WHEN** a configurer opens the `config/` folder
- **THEN** they find `config/ingestion.toml` containing the `[ingestion]` section and `config/embedding.toml` containing the `[chunking]` and `[embedding]` sections
- **AND** no other `config.toml` files exist under `src/`

#### Scenario: No per-module config files remain

- **WHEN** the repository is searched for `config.toml` under `src/`
- **THEN** none are found

### Requirement: Central startup-loaded settings object

The system SHALL provide a single configuration package that loads all TOML and `.env` values once and exposes a typed `settings` object. Application code SHALL read configuration values as attributes of `settings` and SHALL NOT open or parse any configuration file directly.

#### Scenario: Code reads typed attributes

- **WHEN** application code needs a tunable such as the embedding model or ingestion seasons
- **THEN** it reads `settings.embedding.model` or `settings.ingestion.seasons`
- **AND** no module references a TOML file path

#### Scenario: Values are typed

- **WHEN** `settings` is loaded
- **THEN** numeric, list, and string fields are exposed with their declared Python types (e.g. `settings.chunking.max_tokens` is an `int`, `settings.ingestion.seasons` is a `list[str]`)

### Requirement: Unified TOML tunables and environment secrets

The `settings` object SHALL unify TOML tunables and `.env`-derived values, exposing secret-derived values (database URLs, embedding endpoint and key, shared data directory) as distinct typed fields. Loading of `.env` SHALL occur centrally in the configuration package, not via scattered call sites.

#### Scenario: Secrets exposed as explicit fields

- **WHEN** code needs the embedding endpoint or a database URL
- **THEN** it reads the corresponding typed field on `settings`
- **AND** the value originates from the environment / `.env`, never from a committed TOML file

#### Scenario: Single dotenv load

- **WHEN** the application starts
- **THEN** `.env` is loaded exactly once by the configuration package
- **AND** no module makes its own `load_dotenv()` call

### Requirement: Fail-loud validation

The configuration package SHALL validate all required values at load time and raise a clear error if any required TOML section, key, or secret is missing or malformed. The system SHALL assert that the configured embedding dimension matches the schema's `EMBEDDING_DIM` constant so drift fails loudly at startup.

#### Scenario: Missing required value

- **WHEN** a required configuration value is absent or has the wrong type
- **THEN** loading fails with an error naming the offending field

#### Scenario: Embedding dimension drift

- **WHEN** `settings.embedding.dimension` does not equal the `EMBEDDING_DIM` constant declared in the database models
- **THEN** the application fails at startup with an explanatory error
