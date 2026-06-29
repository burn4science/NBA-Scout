import enum
import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    UUID,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

EMBEDDING_DIM = 768


class Base(DeclarativeBase):
    pass


class Scope(enum.StrEnum):
    """Visibility class of a document/chunk."""

    GLOBAL = "global"
    TENANT = "tenant"


class SourceType(enum.StrEnum):
    """Origin of a source document."""

    BIO = "bio"
    SCOUTING_NOTE = "scouting_note"
    DRAFT_EVAL = "draft_eval"


# Shared Enum instances reused across tables so the DDL never emits duplicate
# CREATE TYPE. The enum types themselves are created explicitly in the migration
# (create_type=False), so values_callable pins the lowercase string values.
_scope_enum = Enum(
    Scope,
    name="scope",
    values_callable=lambda e: [m.value for m in e],
    create_type=False,
)
_source_type_enum = Enum(
    SourceType,
    name="source_type",
    values_callable=lambda e: [m.value for m in e],
    create_type=False,
)


class Team(Base):
    __tablename__ = "teams"

    team_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    abbreviation: Mapped[str] = mapped_column(String(10), nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    conference: Mapped[str | None] = mapped_column(String(20))
    division: Mapped[str | None] = mapped_column(String(50))

    season_stats: Mapped[list["PlayerSeasonStats"]] = relationship(back_populates="team")


class Player(Base):
    __tablename__ = "players"

    player_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    first_name: Mapped[str | None] = mapped_column(String(100))
    last_name: Mapped[str | None] = mapped_column(String(100))
    position: Mapped[str | None] = mapped_column(String(20))
    height_cm: Mapped[float | None] = mapped_column(Float)
    weight_kg: Mapped[float | None] = mapped_column(Float)
    birth_date: Mapped[str | None] = mapped_column(Date)
    country: Mapped[str | None] = mapped_column(String(100))
    draft_year: Mapped[int | None] = mapped_column(Integer)
    draft_round: Mapped[int | None] = mapped_column(Integer)
    draft_number: Mapped[int | None] = mapped_column(Integer)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    season_stats: Mapped[list["PlayerSeasonStats"]] = relationship(back_populates="player")
    tenant_access: Mapped[list["TenantPlayer"]] = relationship(back_populates="player")


class Season(Base):
    __tablename__ = "seasons"

    season_id: Mapped[str] = mapped_column(String(10), primary_key=True)

    stats: Mapped[list["PlayerSeasonStats"]] = relationship(back_populates="season")


class PlayerSeasonStats(Base):
    __tablename__ = "player_season_stats"

    player_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("players.player_id"), primary_key=True
    )
    team_id: Mapped[int] = mapped_column(Integer, ForeignKey("teams.team_id"), primary_key=True)
    season_id: Mapped[str] = mapped_column(
        String(10), ForeignKey("seasons.season_id"), primary_key=True
    )

    # Box stats
    games_played: Mapped[int | None] = mapped_column(Integer)
    min_per_game: Mapped[float | None] = mapped_column(Float)
    pts: Mapped[float | None] = mapped_column(Float)
    reb: Mapped[float | None] = mapped_column(Float)
    ast: Mapped[float | None] = mapped_column(Float)
    stl: Mapped[float | None] = mapped_column(Float)
    blk: Mapped[float | None] = mapped_column(Float)
    fg_pct: Mapped[float | None] = mapped_column(Float)
    fg3_pct: Mapped[float | None] = mapped_column(Float)
    ft_pct: Mapped[float | None] = mapped_column(Float)

    # Advanced stats (nullable — not all seasons/endpoints return these)
    per: Mapped[float | None] = mapped_column(Float)
    ts_pct: Mapped[float | None] = mapped_column(Float)
    usg_pct: Mapped[float | None] = mapped_column(Float)
    off_rtg: Mapped[float | None] = mapped_column(Float)
    def_rtg: Mapped[float | None] = mapped_column(Float)

    player: Mapped["Player"] = relationship(back_populates="season_stats")
    team: Mapped["Team"] = relationship(back_populates="season_stats")
    season: Mapped["Season"] = relationship(back_populates="stats")


class Tenant(Base):
    __tablename__ = "tenants"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)

    players: Mapped[list["TenantPlayer"]] = relationship(back_populates="tenant")


class TenantPlayer(Base):
    __tablename__ = "tenant_players"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.tenant_id"), primary_key=True
    )
    player_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("players.player_id"), primary_key=True
    )

    tenant: Mapped["Tenant"] = relationship(back_populates="players")
    player: Mapped["Player"] = relationship(back_populates="tenant_access")


class Document(Base):
    """A source text unit. `scope` decides visibility: global (shared, no owner)
    or tenant (private, owned by exactly one tenant)."""

    __tablename__ = "documents"

    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    player_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("players.player_id"))
    scope: Mapped[Scope] = mapped_column(_scope_enum, nullable=False)
    owner_tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.tenant_id")
    )
    source_type: Mapped[SourceType] = mapped_column(_source_type_enum, nullable=False)
    title: Mapped[str | None] = mapped_column(String(300))
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    chunks: Mapped[list["Chunk"]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint(
            "(scope = 'global' AND owner_tenant_id IS NULL) "
            "OR (scope = 'tenant' AND owner_tenant_id IS NOT NULL)",
            name="ck_documents_scope_owner",
        ),
    )


class Chunk(Base):
    """An embeddable + retrievable unit. `player_id`, `scope`, and
    `owner_tenant_id` are denormalized from the parent document so the retrieval
    hot path needs no join. RLS keys isolation on `owner_tenant_id`."""

    __tablename__ = "chunks"

    chunk_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.document_id", ondelete="CASCADE"),
        nullable=False,
    )
    # Denormalized from the parent document.
    player_id: Mapped[int | None] = mapped_column(Integer)
    scope: Mapped[Scope] = mapped_column(_scope_enum, nullable=False)
    owner_tenant_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))

    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    # `metadata` is reserved on the declarative Base, so the attribute is aliased.
    chunk_metadata: Mapped[dict] = mapped_column(
        "metadata", JSONB, nullable=False, server_default="{}"
    )
    embedding: Mapped[list[float] | None] = mapped_column(Vector(EMBEDDING_DIM))
    embedding_model: Mapped[str | None] = mapped_column(String(200))
    embedding_dim: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    document: Mapped["Document"] = relationship(back_populates="chunks")

    __table_args__ = (
        Index("ix_chunks_player_id", "player_id"),
        Index("ix_chunks_scope_owner", "scope", "owner_tenant_id"),
        Index(
            "ix_chunks_embedding_hnsw",
            "embedding",
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )
