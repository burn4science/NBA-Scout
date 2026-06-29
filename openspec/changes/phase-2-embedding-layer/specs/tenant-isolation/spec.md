## ADDED Requirements

### Requirement: Isolation is enforced by Row-Level Security, not application code
The `documents` and `chunks` tables SHALL have `ROW LEVEL SECURITY` both `ENABLE`d and `FORCE`d, with a `tenant_isolation` policy of the form `USING (scope = 'global' OR owner_tenant_id = current_setting('app.current_tenant', true)::uuid)`. Tenant isolation SHALL NOT depend on application-supplied `WHERE` clauses.

#### Scenario: A buggy query cannot cross tenants
- **WHEN** the application, connected as `nba_app` under tenant A's context, runs a `SELECT * FROM chunks` with no tenant filter in the query text
- **THEN** the database returns only `global` chunks and chunks owned by tenant A

#### Scenario: FORCE applies the policy to the table owner
- **WHEN** the table-owner role queries `chunks` with a tenant context set
- **THEN** the policy still applies (the owner does not bypass RLS)

---

### Requirement: Tenant context is injected dynamically per transaction
The application SHALL set the active tenant via `SET LOCAL app.current_tenant = :tenant_id` inside a transaction (`tenant_session`), so the context is scoped to that transaction and never leaks across connections or requests. A separate `admin_session` with no tenant set SHALL be used for global-scope writes.

#### Scenario: Tenant context is scoped to the transaction
- **WHEN** a `tenant_session(A)` transaction completes and a new `tenant_session(B)` begins on a reused connection
- **THEN** the second transaction sees tenant B's context only, with no residual tenant A context

#### Scenario: Global writes use an admin session
- **WHEN** a `global`-scope document and its chunks are written
- **THEN** they are written via `admin_session` (no tenant context) and are subsequently visible to every tenant

---

### Requirement: Default-deny for private rows when no tenant is set
When `app.current_tenant` is unset, queries against `documents` and `chunks` SHALL return only `global` rows and SHALL NOT return any `tenant`-scoped (private) rows.

#### Scenario: No context yields global-only visibility
- **WHEN** a query runs as `nba_app` with `app.current_tenant` unset
- **THEN** only `scope='global'` rows are returned and no private rows are exposed

#### Scenario: One tenant cannot read another tenant's private chunks
- **WHEN** the application operates under tenant B's context
- **THEN** a read or update targeting a private chunk owned by tenant A affects zero rows
