## 1. Refresh spec wording

- [x] 1.1 In `openspec/specs/embedding-pipeline/spec.md`, update the "Pipeline chunks source text via a swappable Docling chunker" requirement: chunk size/overlap/tokenizer settings come from the central configuration (`config/embedding.toml`, exposed as `settings.chunking`)
- [x] 1.2 Update the "Pipeline generates embeddings via an env-configured OpenAI-compatible endpoint" requirement: `model` and `dimension` (768) come from the central configuration (`config/embedding.toml`, exposed as `settings.embedding`); endpoint/key still from `.env`
- [x] 1.3 Update the "Endpoint is selected by environment without code change" scenario phrase to "no change to code or central config"

## 2. Validate

- [x] 2.1 Run `openspec validate --specs` and confirm all specs pass
