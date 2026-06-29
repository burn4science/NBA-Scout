"""Integration tests: prove Row-Level Security isolates tenants.

Requires the migrated database to be reachable via APP_DATABASE_URL /
MIGRATION_DATABASE_URL (loaded from .env). Uses a fake chunker + the in-memory
embedder, so neither Docling nor a live embedding backend is needed.
"""

import os

import pytest
from dotenv import load_dotenv
from sqlalchemy import text

load_dotenv()

from chunking.protocol import Chunk  # noqa: E402
from db import get_admin_engine, get_app_engine, tenant_session  # noqa: E402
from embed.in_memory import InMemoryEmbedder  # noqa: E402
from embed.pipeline import ensure_tenants, run_pipeline  # noqa: E402
from embed.seed import SEED_TENANTS  # noqa: E402

pytestmark = pytest.mark.skipif(
    not (os.environ.get("APP_DATABASE_URL") and os.environ.get("MIGRATION_DATABASE_URL")),
    reason="APP_DATABASE_URL / MIGRATION_DATABASE_URL not configured",
)


class _FakeChunker:
    def chunk(self, raw_text: str, metadata: dict) -> list[Chunk]:
        return [Chunk(content=raw_text, chunk_index=0, metadata=metadata)]


class _Log:
    def info(self, *args, **kwargs) -> None:  # noqa: D401 - silent logger
        pass


@pytest.fixture()
def tenants() -> dict[str, str]:
    # Clean slate (TRUNCATE bypasses RLS) then seed via the real pipeline path.
    with get_admin_engine().begin() as conn:
        conn.execute(text("TRUNCATE chunks, documents RESTART IDENTITY CASCADE"))
    run_pipeline(_FakeChunker(), InMemoryEmbedder(dimension=768), _Log())
    return {name: str(tid) for name, tid in ensure_tenants(SEED_TENANTS).items()}


def test_set_config_injects_tenant(tenants: dict[str, str]) -> None:
    alpha = tenants["Team Alpha"]
    query = text("SELECT current_setting('app.current_tenant', true)")
    with tenant_session(alpha) as conn:
        value = conn.execute(query).scalar_one()
    assert value == alpha


def test_tenant_sees_only_global_and_own(tenants: dict[str, str]) -> None:
    alpha, beta = tenants["Team Alpha"], tenants["Team Beta"]
    with tenant_session(alpha) as conn:
        rows = conn.execute(text("SELECT scope, owner_tenant_id FROM chunks")).all()
    assert rows, "expected visible chunks for tenant Alpha"
    for scope, owner in rows:
        assert scope == "global" or str(owner) == alpha
    assert all(str(owner) != beta for _, owner in rows)


def test_other_tenant_private_is_invisible(tenants: dict[str, str]) -> None:
    alpha, beta = tenants["Team Alpha"], tenants["Team Beta"]
    with tenant_session(alpha) as conn:
        count = conn.execute(
            text("SELECT count(*) FROM chunks WHERE owner_tenant_id = :b"), {"b": beta}
        ).scalar_one()
    assert count == 0  # RLS, not a WHERE clause, blocks this


def test_default_deny_without_context(tenants: dict[str, str]) -> None:
    # nba_app with no tenant set → only global rows are visible.
    with get_app_engine().connect() as conn:
        scopes = {r[0] for r in conn.execute(text("SELECT DISTINCT scope FROM chunks")).all()}
    assert "tenant" not in scopes
    assert scopes <= {"global"}
