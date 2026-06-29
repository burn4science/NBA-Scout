## ADDED Requirements

### Requirement: Schema defines the documents table
The database SHALL contain a `documents` table with columns: `document_id` (UUID, PK), `player_id` (INTEGER, FK→`players`, nullable), `scope` (ENUM `global`|`tenant`, NOT NULL), `owner_tenant_id` (UUID, FK→`tenants`, nullable), `source_type` (ENUM `bio`|`scouting_note`|`draft_eval`, NOT NULL), `title` (VARCHAR), `raw_text` (TEXT), `created_at` (TIMESTAMP), `updated_at` (TIMESTAMP). A CHECK constraint SHALL enforce `(scope='global' AND owner_tenant_id IS NULL) OR (scope='tenant' AND owner_tenant_id IS NOT NULL)`.

#### Scenario: Documents table exists after migration
- **WHEN** `alembic upgrade head` is run on a fresh database
- **THEN** the `documents` table exists with all specified columns and the scope/owner CHECK constraint

#### Scenario: Global document without an owner is accepted
- **WHEN** a document with `scope='global'` and `owner_tenant_id=NULL` is inserted
- **THEN** the row is accepted

#### Scenario: Tenant document without an owner is rejected
- **WHEN** a document with `scope='tenant'` and `owner_tenant_id=NULL` is inserted
- **THEN** the CHECK constraint rejects the row

---

### Requirement: Schema defines the chunks table
The database SHALL contain a `chunks` table with columns: `chunk_id` (UUID, PK), `document_id` (UUID, FK→`documents`, ON DELETE CASCADE), `player_id` (INTEGER), `scope` (ENUM `global`|`tenant`), `owner_tenant_id` (UUID, nullable), `chunk_index` (INTEGER), `content` (TEXT), `metadata` (JSONB), `embedding` (`vector(768)`), `embedding_model` (VARCHAR), `embedding_dim` (INTEGER), `created_at` (TIMESTAMP). The `player_id`, `scope`, and `owner_tenant_id` columns SHALL be denormalized from the parent document so retrieval queries need no join.

#### Scenario: Chunks table exists after migration
- **WHEN** `alembic upgrade head` is run on a fresh database
- **THEN** the `chunks` table exists with all specified columns including a `vector(768)` embedding column

#### Scenario: Deleting a document removes its chunks
- **WHEN** a `documents` row is deleted
- **THEN** all `chunks` rows referencing it are removed by the ON DELETE CASCADE

#### Scenario: Embedding provenance is recorded
- **WHEN** a chunk is inserted by the pipeline
- **THEN** `embedding_model` and `embedding_dim` reflect the embedder that produced the vector, and `embedding_dim` equals 768

---

### Requirement: Chunk embeddings are indexed with HNSW
The `chunks.embedding` column SHALL have an HNSW index using cosine distance. Btree indexes SHALL exist on `chunks.player_id` and on `chunks(scope, owner_tenant_id)` to support pre-filtered retrieval.

#### Scenario: HNSW index exists after migration
- **WHEN** `alembic upgrade head` completes
- **THEN** an HNSW index on `chunks.embedding` and the supporting btree indexes exist

---

### Requirement: A dedicated non-owner application role exists
The migration SHALL create an application database role (`nba_app`) that is neither a superuser nor the owner of the `documents` and `chunks` tables, granted only DML privileges on those tables (and SELECT on referenced tables). This role is the one the application connects as, so Row-Level Security applies to it.

#### Scenario: App role exists and does not own the tables
- **WHEN** `alembic upgrade head` completes
- **THEN** the `nba_app` role exists, is not a superuser, and is not the owner of `documents` or `chunks`

#### Scenario: Migration is reversible
- **WHEN** `alembic downgrade -1` is run
- **THEN** the `documents` and `chunks` tables, their indexes, the RLS policies, and the `nba_app` role are dropped cleanly
