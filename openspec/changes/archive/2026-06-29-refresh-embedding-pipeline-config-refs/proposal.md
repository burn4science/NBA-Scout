## Why

The archived `centralize-config` change moved all tunables into one `config/` folder loaded through a typed `settings` object, and added a `configuration` capability spec describing it. The `embedding-pipeline` spec still describes the old per-module `config.toml` files ("the chunk module's private `config.toml`", "the embed module's `config.toml`"), which no longer exist. The prose now contradicts both the code and the `configuration` spec. This change realigns that wording. Behavior is unchanged.

## What Changes

- Update the `embedding-pipeline` spec so chunking and embedding tunables are described as coming from the **central configuration** (`config/embedding.toml`, exposed as `settings.chunking` / `settings.embedding`) rather than per-module `config.toml` files.
- Refresh one scenario phrase ("no change to code or `config.toml`" → "no change to code or central config").
- Documentation-only: **no code changes**, no behavior change.

## Capabilities

### New Capabilities
<!-- None. -->

### Modified Capabilities
- `embedding-pipeline`: Requirement descriptions for chunking config source and embedding model/dimension config source are reworded to reference the central configuration; no normative behavior changes.

## Impact

- **Spec only**: `openspec/specs/embedding-pipeline/spec.md`.
- No source, dependency, or test impact.
