# retriever.py

import json
import faiss
import numpy as np
import os
import logging
from typing import List, Dict, Tuple
from openai import OpenAI
from dotenv import load_dotenv

# Load API keys
load_dotenv()

# Logging config
logging.basicConfig(level=logging.INFO, format="🔍 [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Constants
EMBEDDINGS_PATH = "data/embeddings.jsonl"
INDEX_PATH = "data/faiss_index.faiss"
DIMENSION = 1536  # OpenAI text-embedding-3-small dimension
TOP_K = 5

client = OpenAI()


def load_embeddings(path: str) -> Tuple[np.ndarray, List[Dict]]:
    """Load embeddings and metadata from JSONL file."""
    logger.info(f"📥 Loading embeddings from {path}")
    embeddings = []
    metadatas = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            obj = json.loads(line)
            embeddings.append(obj["embedding"])
            metadatas.append(obj["metadata"])
    return np.array(embeddings, dtype="float32"), metadatas


def normalize_embeddings(embeddings: np.ndarray) -> np.ndarray:
    """L2 normalize the embeddings."""
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    return embeddings / norms


def build_faiss_index(embeddings: np.ndarray) -> faiss.IndexFlatIP:
    """Build FAISS index (Inner Product) for normalized embeddings."""
    logger.info("⚙️ Building FAISS index...")
    index = faiss.IndexFlatIP(DIMENSION)
    index.add(embeddings)
    return index


def save_index(index: faiss.IndexFlatIP, path: str):
    faiss.write_index(index, path)
    logger.info(f"💾 FAISS index saved to {path}")


def load_index(path: str) -> faiss.IndexFlatIP:
    logger.info(f"📦 Loading FAISS index from {path}")
    return faiss.read_index(path)


def embed_query(text: str) -> np.ndarray:
    """Embed the query string using OpenAI model."""
    response = client.embeddings.create(input=text, model="text-embedding-3-small")
    return np.array(response.data[0].embedding, dtype="float32")


def query_index(
    query: str, index: faiss.IndexFlatIP, metadatas: List[Dict], top_k: int = TOP_K
) -> List[Dict]:
    """Return top_k relevant chunks for a query."""
    logger.info(f"🔎 Querying index for: {query}")
    query_vec = embed_query(query)
    query_vec = query_vec / np.linalg.norm(query_vec)  # Normalize

    D, I = index.search(np.array([query_vec]), top_k)
    results = []
    for i in I[0]:
        if i < len(metadatas):
            results.append(metadatas[i])
    return results


def build_and_save():
    """Full pipeline: load embeddings, build index, save it."""
    embeddings, metadatas = load_embeddings(EMBEDDINGS_PATH)
    embeddings = normalize_embeddings(embeddings)
    index = build_faiss_index(embeddings)
    save_index(index, INDEX_PATH)
    return index, metadatas


if __name__ == "__main__":
    index, metadatas = build_and_save()
