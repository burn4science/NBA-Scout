import uuid

from sqlalchemy import (
    UUID,
    Boolean,
    Date,
    Float,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


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
