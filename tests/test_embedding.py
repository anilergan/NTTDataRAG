import pytest
from embedding import embed_chunks


def test_embed_chunks_output_shape():
    dummy_chunks = [
        {"content": "NTT is a global technology company."},
        {"content": "They work on AI and data solutions."},
    ]
    embeddings = embed_chunks(dummy_chunks)

    assert isinstance(embeddings, list)
    assert len(embeddings) == 2
    for emb in embeddings:
        assert isinstance(emb, dict)
        assert "embedding" in emb
        assert isinstance(emb["embedding"], list)
        assert "metadata" in emb
        assert isinstance(emb["metadata"], dict)

