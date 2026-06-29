## MODIFIED Requirements

### Requirement: Pipeline chunks source text via a swappable Docling chunker
The pipeline SHALL split a document's `raw_text` into ordered chunks using Docling, accessed through a `Chunker` protocol so the chunking implementation can be replaced without changing the pipeline. Chunk size, overlap, and tokenizer settings SHALL come from the central configuration (`config/embedding.toml`, exposed as `settings.chunking`).

#### Scenario: A document is chunked into ordered units
- **WHEN** the pipeline processes a document's `raw_text`
- **THEN** one or more `chunks` rows are produced with monotonically increasing `chunk_index` and non-empty `content`

#### Scenario: Chunker is swappable behind the protocol
- **WHEN** an alternative `Chunker` implementation is supplied to the pipeline
- **THEN** the pipeline runs unchanged and produces chunks from that implementation

### Requirement: Pipeline generates embeddings via an env-configured OpenAI-compatible endpoint
The pipeline SHALL produce embeddings through an `Embedder` protocol backed by a single OpenAI-compatible client. The endpoint (`EMBEDDING_BASE_URL`) and API key (`EMBEDDING_API_KEY`) SHALL come from `.env`, never from TOML, so the same image runs against a local LM Studio instance or Ollama Cloud with no code change and no rebuild. The `model` and `dimension` (768) SHALL come from the central configuration (`config/embedding.toml`, exposed as `settings.embedding`). The model SHALL be `embeddinggemma-300m`.

#### Scenario: Embeddings are generated at the configured dimension
- **WHEN** the pipeline embeds chunk text
- **THEN** each returned vector has length 768 and is stored in the `chunks.embedding` column

#### Scenario: Endpoint is selected by environment without code change
- **WHEN** `EMBEDDING_BASE_URL` and `EMBEDDING_API_KEY` point at Ollama Cloud instead of LM Studio
- **THEN** the embedder targets that endpoint with no change to code or central config

#### Scenario: Dimension mismatch is rejected
- **WHEN** the endpoint returns a vector whose length does not equal the configured `dimension`
- **THEN** the embedder raises an error rather than storing a malformed vector
