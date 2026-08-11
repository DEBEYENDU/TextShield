"""Tests for the RAG pipeline: embeddings, vector store, retrieval."""
from __future__ import annotations

import pytest

from app.rag.embeddings import HashingEmbeddings
from app.rag.vector_store import SimpleVectorStore


@pytest.fixture()
def store(tmp_path):
    return SimpleVectorStore(tmp_path / "vec")


@pytest.fixture()
def provider():
    return HashingEmbeddings()


def test_hashing_embeddings_shape_and_norm(provider):
    vectors = provider.embed(["hello world", "another message"])
    assert vectors.shape == (2, provider.dimension)
    norms = (vectors * vectors).sum(axis=1)
    assert pytest.approx(1.0, abs=1e-4) == norms[0]


def test_hashing_is_deterministic(provider):
    a = provider.embed_one("Attack of the clones")
    b = provider.embed_one("Attack of the clones")
    assert (a == b).all()


def test_similar_texts_are_closer(provider):
    base = provider.embed_one("your bank account has been blocked, verify now")
    similar = provider.embed_one("your bank account was blocked, verify immediately")
    unrelated = provider.embed_one("hey are we meeting at five pm today")
    sim_score = (base * similar).sum()
    diff_score = (base * unrelated).sum()
    assert sim_score > diff_score


def test_store_add_and_count(store, provider):
    store.add(["a", "b"], provider.embed(["first doc", "second doc"]),
              ["first doc", "second doc"], [{"category": "x"}, {"category": "y"}])
    assert store.count == 2


def test_store_query_returns_top_k_sorted(store, provider):
    docs = [
        "your bank account will be blocked, verify immediately",
        "your parcel is stuck at customs, pay the fee",
        "are we meeting at 5 pm today",
    ]
    store.add(
        [f"id{i}" for i in range(len(docs))],
        provider.embed(docs),
        docs,
        [{"category": "banking_scams"}, {"category": "delivery"}, {"category": "chat"}],
    )
    hits = store.query(provider.embed_one("your bank account has been blocked, click to verify"), top_k=2)
    assert len(hits) == 2
    assert hits[0]["score"] >= hits[1]["score"]
    assert hits[0]["metadata"]["category"] == "banking_scams"


def test_store_empty_query(store, provider):
    assert store.query(provider.embed_one("anything"), top_k=3) == []


def test_store_delete_all(store, provider):
    store.add(["a"], provider.embed(["doc"]), ["doc"], [{"category": "x"}])
    store.delete_all()
    assert store.count == 0
    assert store.query(provider.embed_one("x"), top_k=1) == []


def test_retriever_status_and_retrieve(tmp_path, provider, monkeypatch):
    from app.core import config as config_mod
    from app.rag import retriever as retriever_mod

    build_dir = tmp_path / "kb"
    build_dir.mkdir()
    (build_dir / "banking_scams").mkdir()
    (build_dir / "banking_scams" / "note.md").write_text(
        "your bank account has been blocked, verify immediately using this link",
        encoding="utf-8",
    )
    from app.rag.embeddings import create_embedding_provider
    from app.rag.vector_store import open_vector_store

    monkeypatch.setattr(config_mod.settings, "EMBEDDING_PROVIDER", "hashing")
    monkeypatch.setattr(config_mod.settings, "VECTOR_DB_PATH", tmp_path / "vec2")
    store = open_vector_store(tmp_path / "vec2")
    store.delete_all()
    chunks = ["your bank account has been blocked, verify immediately using this link"]
    store.add(["c0"], provider.embed(chunks), chunks,
              [{"source": "note.md", "category": "banking_scams"}])
    store.save_structure(
        {"chunk_count": 1, "document_count": 1, "categories": ["banking_scams"],
         "built_at": "2026-01-01T00:00:00Z", "embedding_provider": "hashing",
         "backend": store.backend_name}
    )

    r = retriever_mod.Retriever()
    hits = r.retrieve("your bank account is blocked, verify now", top_k=1)
    assert hits
    assert hits[0]["category"] == "banking_scams"
    assert hits[0]["source"] == "note.md"
    assert hits[0]["score"] > 0.3