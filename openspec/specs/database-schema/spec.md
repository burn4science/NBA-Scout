# Spec: Database Schema

## Purpose

The database schema capability defines the relational structure of the NBA Scout application database. It covers all tables, constraints, foreign keys, and extensions required by the data ingestion and multi-tenant access control model. All DDL is managed via SQLAlchemy ORM models and Alembic migrations.

## Requirements

### Requirement: Schema defines the teams table
The database SHALL contain a `teams` table with columns: `team_id` (INTEGER, PK), `abbreviation` (VARCHAR), `city` (VARCHAR), `full_name` (VARCHAR), `conference` (VARCHAR), `division` (VARCHAR).

#### Scenario: Teams table exists after migration
- **WHEN** `alembic upgrade head` is run on a fresh database
- **THEN** the `teams` table exists with all specified columns and the correct types

---

### Requirement: Schema defines the players table
The database SHALL contain a `players` table with columns: `player_id` (INTEGER, PK), `full_name` (VARCHAR NOT NULL), `first_name` (VARCHAR), `last_name` (VARCHAR), `position` (VARCHAR), `height_cm` (FLOAT), `weight_kg` (FLOAT), `birth_date` (DATE), `country` (VARCHAR), `draft_year` (INTEGER, nullable), `draft_round` (INTEGER, nullable), `draft_number` (INTEGER, nullable), `is_active` (BOOLEAN NOT NULL DEFAULT FALSE).

#### Scenario: Players table exists after migration
- **WHEN** `alembic upgrade head` is run on a fresh database
- **THEN** the `players` table exists with all specified columns

#### Scenario: Undrafted players are stored without error
- **WHEN** a player has no draft data
- **THEN** `draft_year`, `draft_round`, and `draft_number` are NULL without constraint violation

---

### Requirement: Schema defines the seasons table
The database SHALL contain a `seasons` table with columns: `season_id` (VARCHAR, PK, e.g. `"2024-25"`). This table acts as a reference for foreign keys in `player_season_stats`.

#### Scenario: Seasons table is populated at ingestion time
- **WHEN** the pipeline runs for the configured season list
- **THEN** each season string exists as a row in the `seasons` table before any stats rows are inserted

---

### Requirement: Schema defines the player_season_stats table
The database SHALL contain a `player_season_stats` table with a composite PK of `(player_id, team_id, season_id)`. It SHALL include box stat columns (`games_played`, `min_per_game`, `pts`, `reb`, `ast`, `stl`, `blk`, `fg_pct`, `fg3_pct`, `ft_pct`) and advanced stat columns (`per`, `ts_pct`, `usg_pct`, `off_rtg`, `def_rtg`). All advanced stat columns SHALL be nullable. FKs to `players(player_id)`, `teams(team_id)`, and `seasons(season_id)`.

#### Scenario: Stats table has correct composite key
- **WHEN** a duplicate `(player_id, team_id, season_id)` row is inserted
- **THEN** the upsert updates the existing row rather than creating a duplicate

#### Scenario: Advanced stat columns accept NULL
- **WHEN** a player row is inserted without advanced stats
- **THEN** the row is accepted with NULL values in the advanced columns

---

### Requirement: Schema defines the tenants and tenant_players tables
The database SHALL contain a `tenants` table (`tenant_id` UUID PK, `name` VARCHAR NOT NULL) and a `tenant_players` table (`tenant_id` UUID FK, `player_id` INTEGER FK, composite PK). These tables stub the multi-tenant access control model for future enforcement.

#### Scenario: Tenant tables exist after migration
- **WHEN** `alembic upgrade head` is run
- **THEN** both `tenants` and `tenant_players` tables exist with correct PKs and FKs

#### Scenario: tenant_players enforces referential integrity
- **WHEN** a row is inserted into `tenant_players` with a non-existent `player_id`
- **THEN** the database raises a foreign key constraint violation

---

### Requirement: pgvector extension is enabled
The database SHALL have the `pgvector` extension installed and enabled on the target schema. No vector indices are created in this phase — extension availability is the only requirement.

#### Scenario: Extension is available after migration
- **WHEN** `alembic upgrade head` completes
- **THEN** `SELECT * FROM pg_extension WHERE extname = 'pgvector'` returns one row

---

### Requirement: All schema changes are managed via Alembic
The schema SHALL be defined exclusively through SQLAlchemy ORM models. All DDL changes SHALL be applied via Alembic migrations. No raw `CREATE TABLE` statements outside of generated migration files are permitted.

#### Scenario: Fresh database is fully migrated by one command
- **WHEN** `uv run alembic upgrade head` is run against an empty database
- **THEN** all tables, constraints, and extensions exist with no manual intervention

#### Scenario: Migration is reversible
- **WHEN** `uv run alembic downgrade base` is run
- **THEN** all tables created by this change are dropped cleanly
