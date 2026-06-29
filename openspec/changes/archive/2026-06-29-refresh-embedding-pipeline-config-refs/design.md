## Context

Documentation-only realignment. The `embedding-pipeline` spec predates `centralize-config` and still references per-module `config.toml` files that have been removed. No technical design is required; this records the trivial approach for completeness.

## Goals / Non-Goals

**Goals:**
- Make the `embedding-pipeline` spec consistent with the `configuration` capability and the current code.

**Non-Goals:**
- Any code, dependency, or behavior change.
- Changing normative requirements (the SHALL clauses keep their meaning; only the config *source* wording changes).

## Decisions

- Edit the two affected requirement descriptions in place via a `## MODIFIED Requirements` delta, copying each full requirement block (description + all scenarios) so archive-time merge keeps every scenario. Alternative — a free-text errata note — rejected because the spec is the source of truth and must read correctly on its own.

## Risks / Trade-offs

- [Accidental scenario loss at archive merge] → Include the complete requirement block (all scenarios) in the MODIFIED delta, not just the changed sentence.
