"""Database engines and tenant-scoped sessions.

Isolation is enforced by Postgres Row-Level Security, not by application code.
The app connects through the non-owner ``nba_app`` role (``APP_DATABASE_URL``)
so the RLS policy applies to it; ``tenant_session`` injects the active tenant
into the transaction via ``set_config('app.current_tenant', ..., true)`` (the
parameterizable, transaction-local equivalent of ``SET LOCAL``).
"""

from __future__ import annotations

import os
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from functools import lru_cache

from sqlalchemy import Connection, Engine, create_engine, text


class DatabaseConfigError(RuntimeError):
    """Raised when a required database URL is not configured."""


def _require_url(var: str) -> str:
    url = os.environ.get(var)
    if not url:
        raise DatabaseConfigError(f"{var} is not set. Copy .env.example to .env and configure it.")
    return url


@lru_cache(maxsize=1)
def get_app_engine() -> Engine:
    """Engine for the non-owner application role — RLS is enforced against it."""
    return create_engine(_require_url("APP_DATABASE_URL"))


@lru_cache(maxsize=1)
def get_admin_engine() -> Engine:
    """Engine for the privileged/migration role, used for global-scope writes.
    Still subject to FORCE RLS, so it can only read/write global rows."""
    return create_engine(_require_url("MIGRATION_DATABASE_URL"))


@contextmanager
def tenant_session(tenant_id: uuid.UUID | str) -> Iterator[Connection]:
    """Transaction bound to a tenant: RLS restricts visibility to global rows
    plus rows owned by ``tenant_id``."""
    engine = get_app_engine()
    with engine.begin() as conn:
        conn.execute(
            text("SELECT set_config('app.current_tenant', :tid, true)"),
            {"tid": str(tenant_id)},
        )
        yield conn


@contextmanager
def admin_session() -> Iterator[Connection]:
    """Transaction with no tenant context (global scope). Under default-deny,
    only global rows are visible; only global rows may be written."""
    engine = get_admin_engine()
    with engine.begin() as conn:
        yield conn
