"""initial schema

Revision ID: a1b2c3d4e5f6
Revises:
Create Date: 2026-06-28

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "a1b2c3d4e5f6"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "teams",
        sa.Column("team_id", sa.Integer(), nullable=False),
        sa.Column("abbreviation", sa.String(length=10), nullable=False),
        sa.Column("city", sa.String(length=100), nullable=False),
        sa.Column("full_name", sa.String(length=100), nullable=False),
        sa.Column("conference", sa.String(length=20), nullable=True),
        sa.Column("division", sa.String(length=50), nullable=True),
        sa.PrimaryKeyConstraint("team_id"),
    )

    op.create_table(
        "players",
        sa.Column("player_id", sa.Integer(), nullable=False),
        sa.Column("full_name", sa.String(length=200), nullable=False),
        sa.Column("first_name", sa.String(length=100), nullable=True),
        sa.Column("last_name", sa.String(length=100), nullable=True),
        sa.Column("position", sa.String(length=20), nullable=True),
        sa.Column("height_cm", sa.Float(), nullable=True),
        sa.Column("weight_kg", sa.Float(), nullable=True),
        sa.Column("birth_date", sa.Date(), nullable=True),
        sa.Column("country", sa.String(length=100), nullable=True),
        sa.Column("draft_year", sa.Integer(), nullable=True),
        sa.Column("draft_round", sa.Integer(), nullable=True),
        sa.Column("draft_number", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("player_id"),
    )

    op.create_table(
        "seasons",
        sa.Column("season_id", sa.String(length=10), nullable=False),
        sa.PrimaryKeyConstraint("season_id"),
    )

    op.create_table(
        "tenants",
        sa.Column("tenant_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.PrimaryKeyConstraint("tenant_id"),
    )

    op.create_table(
        "player_season_stats",
        sa.Column("player_id", sa.Integer(), nullable=False),
        sa.Column("team_id", sa.Integer(), nullable=False),
        sa.Column("season_id", sa.String(length=10), nullable=False),
        sa.Column("games_played", sa.Integer(), nullable=True),
        sa.Column("min_per_game", sa.Float(), nullable=True),
        sa.Column("pts", sa.Float(), nullable=True),
        sa.Column("reb", sa.Float(), nullable=True),
        sa.Column("ast", sa.Float(), nullable=True),
        sa.Column("stl", sa.Float(), nullable=True),
        sa.Column("blk", sa.Float(), nullable=True),
        sa.Column("fg_pct", sa.Float(), nullable=True),
        sa.Column("fg3_pct", sa.Float(), nullable=True),
        sa.Column("ft_pct", sa.Float(), nullable=True),
        sa.Column("per", sa.Float(), nullable=True),
        sa.Column("ts_pct", sa.Float(), nullable=True),
        sa.Column("usg_pct", sa.Float(), nullable=True),
        sa.Column("off_rtg", sa.Float(), nullable=True),
        sa.Column("def_rtg", sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(["player_id"], ["players.player_id"]),
        sa.ForeignKeyConstraint(["team_id"], ["teams.team_id"]),
        sa.ForeignKeyConstraint(["season_id"], ["seasons.season_id"]),
        sa.PrimaryKeyConstraint("player_id", "team_id", "season_id"),
    )

    op.create_table(
        "tenant_players",
        sa.Column("tenant_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("player_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.tenant_id"]),
        sa.ForeignKeyConstraint(["player_id"], ["players.player_id"]),
        sa.PrimaryKeyConstraint("tenant_id", "player_id"),
    )


def downgrade() -> None:
    op.drop_table("tenant_players")
    op.drop_table("player_season_stats")
    op.drop_table("tenants")
    op.drop_table("seasons")
    op.drop_table("players")
    op.drop_table("teams")
