## ADDED Requirements

### Requirement: Pipeline fetches and stores team data
The pipeline SHALL fetch all current NBA teams from `nba_api` and upsert them into the `teams` table, including team ID, abbreviation, city, full name, conference, and division.

#### Scenario: Teams are fetched successfully
- **WHEN** the ingestion pipeline runs
- **THEN** all 30 NBA teams are present in the `teams` table with complete metadata

#### Scenario: Re-run is idempotent
- **WHEN** the pipeline runs a second time without data changes
- **THEN** the `teams` table row count remains unchanged and no errors are raised

---

### Requirement: Pipeline fetches and stores player biographical data
The pipeline SHALL fetch biographical data for all players (active and historical) from `nba_api` and upsert them into the `players` table, including player ID, full name, position, height, weight, birth date, country of origin, draft year, draft round, draft number, and active status.

#### Scenario: Active players are stored
- **WHEN** the pipeline runs
- **THEN** all currently active NBA players appear in the `players` table with `is_active = TRUE`

#### Scenario: Historical players are stored
- **WHEN** the pipeline runs
- **THEN** players with no current roster assignment appear with `is_active = FALSE`

#### Scenario: Re-run is idempotent
- **WHEN** the pipeline runs a second time
- **THEN** existing player rows are updated in place, not duplicated

---

### Requirement: Pipeline fetches per-season box and advanced stats
The pipeline SHALL fetch per-season statistics for all players across the configured season list and upsert merged rows into `player_season_stats`. Each row SHALL combine box stats (points, rebounds, assists, steals, blocks, shooting percentages) and advanced stats (PER, TS%, USG%, DRTG, ORTG) for a single `(player_id, team_id, season_id)` combination.

#### Scenario: Stats are fetched for all configured seasons
- **WHEN** `config.toml` lists five seasons and the pipeline runs
- **THEN** `player_season_stats` contains rows for each season for every player who appeared in that season

#### Scenario: Advanced stats unavailable for a season
- **WHEN** an advanced stats endpoint returns no data for a given season
- **THEN** the row is still inserted with advanced columns set to NULL and a WARNING is logged

#### Scenario: Player traded mid-season appears twice
- **WHEN** a player played for two teams in the same season
- **THEN** two separate rows exist in `player_season_stats` — one per team — both with valid stats

#### Scenario: Re-run is idempotent
- **WHEN** the pipeline re-fetches a season already present in the database
- **THEN** existing rows are updated via upsert and no duplicates are created

---

### Requirement: Pipeline respects API rate limits
The pipeline SHALL insert a configurable delay between consecutive `nba_api` calls and SHALL retry failed requests with exponential backoff before logging a failure and continuing.

#### Scenario: Rate limit delay is applied
- **WHEN** the pipeline makes consecutive API calls
- **THEN** a sleep of at least `rate_limit_delay_seconds` (from config) is applied between each call

#### Scenario: Transient API failure is retried
- **WHEN** an `nba_api` call fails with a timeout or HTTP 429
- **THEN** the pipeline retries up to `max_retries` times with exponential backoff before logging an ERROR and skipping that call

#### Scenario: Non-retryable failure is logged and skipped
- **WHEN** an API call fails after all retries are exhausted
- **THEN** an ERROR is logged with the season and endpoint name, and the pipeline continues to the next item without raising

---

### Requirement: Pipeline is fully configurable via config.toml
The pipeline SHALL read all tunable parameters exclusively from `config/config.toml`. No hardcoded values for seasons, delays, or batch sizes are permitted in application code.

#### Scenario: Season list is configurable
- **WHEN** `config.toml` contains a `seasons` list
- **THEN** the pipeline fetches stats for exactly those seasons and no others

#### Scenario: Rate limit delay is configurable
- **WHEN** `rate_limit_delay_seconds` is set in `config.toml`
- **THEN** that value is used as the inter-call sleep duration

#### Scenario: Missing config key raises at startup
- **WHEN** a required config key is absent from `config.toml`
- **THEN** the pipeline raises a `ConfigurationError` with a descriptive message before making any API calls

---

### Requirement: Pipeline emits structured logs via loguru
The pipeline SHALL log all significant events (startup, per-season progress, errors, completion summary) via `loguru` to both a console sink and a rotating file sink.

#### Scenario: Progress is visible per season
- **WHEN** the pipeline processes a season
- **THEN** an INFO log is emitted at the start and end of each season's fetch with player and row counts

#### Scenario: Errors are distinguishable from warnings
- **WHEN** an API call is retried due to a transient error
- **THEN** a WARNING is logged; when all retries are exhausted, an ERROR is logged
