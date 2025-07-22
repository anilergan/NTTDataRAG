import pytest
from retriever import build_and_save
import faiss

def test_build_and_save_returns_index():
    index, metadata = build_and_save()
    assert isinstance(index, faiss.IndexFlatIP)
    assert isinstance(metadata, list)
    assert len(metadata) > 0
