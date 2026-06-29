import pytest

from appconfig.models import EmbeddingConfig
from appconfig.settings import settings
from embed.in_memory import InMemoryEmbedder
from embed.openai_compatible import EmbeddingError, OpenAICompatibleEmbedder

_CFG = EmbeddingConfig(model="m", dimension=768, timeout_seconds=30, batch_size=32)


def test_in_memory_embedder_dimension_and_determinism() -> None:
    embedder = InMemoryEmbedder(dimension=768)
    a1 = embedder.embed(["hello"])
    a2 = embedder.embed(["hello"])
    assert len(a1) == 1
    assert len(a1[0]) == 768
    assert a1 == a2  # deterministic
    assert embedder.embed(["x", "y"]) != embedder.embed(["y", "x"])


def test_missing_base_url_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    # Secrets are loaded once at import, so simulate "unset" on the loaded object.
    monkeypatch.setattr(settings.secrets, "embedding_base_url", None)
    with pytest.raises(EmbeddingError, match="EMBEDDING_BASE_URL"):
        OpenAICompatibleEmbedder(config=_CFG)


class _FakeData:
    def __init__(self, vec):
        self.embedding = vec


class _FakeResponse:
    def __init__(self, vecs):
        self.data = [_FakeData(v) for v in vecs]


class _FakeEmbeddings:
    def __init__(self, dim):
        self._dim = dim

    def create(self, model, input):  # noqa: A002 - mirrors openai signature
        return _FakeResponse([[0.0] * self._dim for _ in input])


class _FakeClient:
    def __init__(self, dim):
        self.embeddings = _FakeEmbeddings(dim)


def _embedder(dim_returned: int) -> OpenAICompatibleEmbedder:
    embedder = OpenAICompatibleEmbedder(config=_CFG, base_url="http://fake/v1", api_key="x")
    embedder._client = _FakeClient(dim_returned)
    return embedder


def test_correct_dimension_passes() -> None:
    out = _embedder(768).embed(["a", "b"])
    assert len(out) == 2 and all(len(v) == 768 for v in out)


def test_dimension_mismatch_raises() -> None:
    with pytest.raises(EmbeddingError, match="384"):
        _embedder(384).embed(["a"])
