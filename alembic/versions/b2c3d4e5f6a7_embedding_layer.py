"""embedding layer: documents, chunks, RLS, nba_app role

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-06-29

"""

import os
from collections.abc import Sequence

import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "b2c3d4e5f6a7"
down_revision: str | None = "a1b2c3d4e5f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

EMBEDDING_DIM = 768

# Tables that carry tenant data and are governed by Row-Level Security.
_RLS_TABLES = ("documents", "chunks")

scope_enum = postgresql.ENUM("global", "tenant", name="scope", create_type=False)
source_type_enum = postgresql.ENUM(
    "bio", "scouting_note", "draft_eval", name="source_type", create_type=False
)


def upgrade() -> None:
    bind = op.get_bind()
    scope_enum.create(bind, checkfirst=True)
    source_type_enum.create(bind, checkfirst=True)

    op.create_table(
        "documents",
        sa.Column("document_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("player_id", sa.Integer(), nullable=True),
        sa.Column("scope", scope_enum, nullable=False),
        sa.Column("owner_tenant_id", sa.UUID(as_uuid=True), nullable=True),
        sa.Column("source_type", source_type_enum, nullable=False),
        sa.Column("title", sa.String(length=300), nullable=True),
        sa.Column("raw_text", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["player_id"], ["players.player_id"]),
        sa.ForeignKeyConstraint(["owner_tenant_id"], ["tenants.tenant_id"]),
        sa.PrimaryKeyConstraint("document_id"),
        sa.CheckConstraint(
            "(scope = 'global' AND owner_tenant_id IS NULL) "
            "OR (scope = 'tenant' AND owner_tenant_id IS NOT NULL)",
            name="ck_documents_scope_owner",
        ),
    )

    op.create_table(
        "chunks",
        sa.Column("chunk_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("document_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("player_id", sa.Integer(), nullable=True),
        sa.Column("scope", scope_enum, nullable=False),
        sa.Column("owner_tenant_id", sa.UUID(as_uuid=True), nullable=True),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("metadata", postgresql.JSONB(), server_default="{}", nullable=False),
        sa.Column("embedding", Vector(EMBEDDING_DIM), nullable=True),
        sa.Column("embedding_model", sa.String(length=200), nullable=True),
        sa.Column("embedding_dim", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["documents.document_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("chunk_id"),
    )

    op.create_index("ix_chunks_player_id", "chunks", ["player_id"])
    op.create_index("ix_chunks_scope_owner", "chunks", ["scope", "owner_tenant_id"])
    op.create_index(
        "ix_chunks_embedding_hnsw",
        "chunks",
        ["embedding"],
        postgresql_using="hnsw",
        postgresql_with={"m": 16, "ef_construction": 64},
        postgresql_ops={"embedding": "vector_cosine_ops"},
    )

    _create_app_role()
    _enable_rls()


def _create_app_role() -> None:
    """Create the locked-down, non-owner application role. RLS applies to it
    because it is neither superuser nor the owner of the tables."""
    # Password comes from the environment at migration time; never committed.
    app_pwd = os.environ.get("APP_DB_PASSWORD", "nba_app").replace("'", "''")
    op.execute(
        f"""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'nba_app') THEN
                CREATE ROLE nba_app LOGIN PASSWORD '{app_pwd}';
            END IF;
        END
        $$;
        """
    )
    op.execute("GRANT USAGE ON SCHEMA public TO nba_app")
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON documents, chunks TO nba_app")
    op.execute("GRANT SELECT ON players, teams, seasons, tenants TO nba_app")


def _enable_rls() -> None:
    """Enable + FORCE RLS and install the tenant_isolation policy. FORCE makes
    even the table owner subject to the policy. NULLIF collapses an absent tenant
    context to NULL, yielding default-deny (global-only): once a custom GUC has
    been set in a session its reset value is the empty string, and ''::uuid would
    otherwise raise instead of failing closed."""
    for table in _RLS_TABLES:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        op.execute(
            f"""
            CREATE POLICY tenant_isolation ON {table}
            USING (
                scope = 'global'
                OR owner_tenant_id
                   = NULLIF(current_setting('app.current_tenant', true), '')::uuid
            )
            """
        )


def downgrade() -> None:
    for table in _RLS_TABLES:
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation ON {table}")

    op.drop_index("ix_chunks_embedding_hnsw", table_name="chunks")
    op.drop_index("ix_chunks_scope_owner", table_name="chunks")
    op.drop_index("ix_chunks_player_id", table_name="chunks")
    op.drop_table("chunks")
    op.drop_table("documents")

    # Remove all privileges granted to the role in this database, then drop it.
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT FROM pg_roles WHERE rolname = 'nba_app') THEN
                EXECUTE 'DROP OWNED BY nba_app';
                DROP ROLE nba_app;
            END IF;
        END
        $$;
        """
    )

    bind = op.get_bind()
    source_type_enum.drop(bind, checkfirst=True)
    scope_enum.drop(bind, checkfirst=True)
