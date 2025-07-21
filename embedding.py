# embedding.py
import json
import os
import logging
from typing import List, Dict
from pathlib import Path
from tqdm import tqdm
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables (like OPENAI_API_KEY)
load_dotenv()

# Configure logger
logging.basicConfig(level=logging.INFO, format="📘 [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# === Constants ===
CHUNKS_PATH = "data/merged_chunks.jsonl"
EMBEDDINGS_PATH = "data/embeddings.jsonl"
EMBED_MODEL = "text-embedding-3-small"

# === Init OpenAI client ===
client = OpenAI()

def load_chunks(path: str) -> List[Dict]:
    """Load JSONL chunks from file."""
    logger.info(f"📥 Loading chunks from: {path}")
    chunks = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            # Skip chunks with empty content
            if not obj.get("content"):
                continue
            chunks.append(obj)
    logger.info(f"✅ Loaded {len(chunks)} valid chunks.")
    return chunks


def embed_chunk(content: str) -> List[float]:
    """Embed a single chunk using OpenAI API."""
    response = client.embeddings.create(input=content, model=EMBED_MODEL)
    return response.data[0].embedding


def embed_chunks(chunks: List[Dict]) -> List[Dict]:
    """Embed all chunks with metadata."""
    logger.info("🚀 Starting embedding process...")
    embedded = []
    for chunk in tqdm(chunks):
        try:
            vector = embed_chunk(chunk["content"])
            embedded.append({
                "embedding": vector,
                "metadata": {
                    "main_title_of_page": chunk.get("main_title_of_page", ""),
                    "main_subtitle_of_page": chunk.get("main_subtitle_of_page", ""),
                    "header": chunk.get("header", ""),
                    "page": chunk.get("page"),
                    "source": chunk.get("source"),
                }
            })
        except Exception as e:
            logger.warning(f"⚠️ Failed to embed chunk on page {chunk.get('page')}: {e}")
    logger.info(f"✅ Embedded {len(embedded)} chunks.")
    return embedded


def save_embeddings(vectors: List[Dict], path: str):
    """Save embeddings as JSONL."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for vec in vectors:
            json.dump(vec, f)
            f.write("\n")
    logger.info(f"💾 Embeddings saved to: {path}")


def main():
    chunks = load_chunks(CHUNKS_PATH)
    vectors = embed_chunks(chunks)
    save_embeddings(vectors, EMBEDDINGS_PATH)


if __name__ == "__main__":
    main()
