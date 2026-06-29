"""Placeholder seed content for the embedding layer.

Deliberately minimal: enough to exercise both visibility classes (global vs
tenant) and prove cross-tenant isolation. Real bios and scouting notes replace
this later without changing the pipeline or schema. `player_id` is left None
here so seeding does not depend on ingested player rows.
"""

from __future__ import annotations

from dataclasses import dataclass

from db.models import Scope, SourceType

# Seed tenants (created if absent at pipeline time).
SEED_TENANTS: tuple[str, ...] = ("Team Alpha", "Team Beta")


@dataclass(frozen=True)
class SeedDocument:
    title: str
    raw_text: str
    scope: Scope
    source_type: SourceType
    owner_tenant_name: str | None = None  # required iff scope is TENANT
    player_id: int | None = None


# Shared, visible to every tenant — embedded once.
GLOBAL_DOCUMENTS: tuple[SeedDocument, ...] = (
    SeedDocument(
        title="Placeholder Player Bio A",
        raw_text=(
            "# Player A\n\n"
            "Placeholder biographical summary. A versatile wing known for "
            "perimeter shooting and transition defense. This text exists only to "
            "exercise the global embedding path and will be replaced with real "
            "biographical content."
        ),
        scope=Scope.GLOBAL,
        source_type=SourceType.BIO,
    ),
    SeedDocument(
        title="Placeholder Player Bio B",
        raw_text=(
            "# Player B\n\n"
            "Placeholder biographical summary. A traditional center with strong "
            "rim protection and rebounding. Used to validate that shared content "
            "is embedded a single time and visible across all tenants."
        ),
        scope=Scope.GLOBAL,
        source_type=SourceType.BIO,
    ),
)

# Private scouting notes — each owned by exactly one tenant.
TENANT_DOCUMENTS: tuple[SeedDocument, ...] = (
    SeedDocument(
        title="Alpha internal note — Player A",
        raw_text=(
            "## Confidential — Team Alpha\n\n"
            "Internal evaluation: elite closeout speed, target as a 3-and-D "
            "rotation piece. This note must never be visible to other tenants."
        ),
        scope=Scope.TENANT,
        source_type=SourceType.SCOUTING_NOTE,
        owner_tenant_name="Team Alpha",
    ),
    SeedDocument(
        title="Beta internal note — Player B",
        raw_text=(
            "## Confidential — Team Beta\n\n"
            "Internal evaluation: anchors a drop-coverage scheme, limited switch "
            "ability. This note belongs solely to Team Beta."
        ),
        scope=Scope.TENANT,
        source_type=SourceType.SCOUTING_NOTE,
        owner_tenant_name="Team Beta",
    ),
)
