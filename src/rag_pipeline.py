# rag_pipeline.py

import json
import logging
import os

import faiss
from dotenv import load_dotenv
from openai import OpenAI

# --- your embedding & index utilities ---
from src.embedding import embed_chunks, save_embeddings

# --- your custom chunker ---
from src.pdf_chunker_by_template import extract_chunks_by_template
from src.query import interactive_qa_loop
from src.retriever import build_and_save

# --- CONFIGURATION (adjust per‐PDF) ---
PDF_PATH = "data/raw/sr_2020_cb_p.pdf"

PAGES_TO_USE = list(range(6, 16)) + list(range(17, 28)) + list(range(29, 36))
SECTION_COORDINATES_DICT = {
    "main_title_of_page": ((40, 115), (338, 270)),
    "main_subtitle_of_page": ((350, 115), (1500, 270)),
    "social_issues": ((250, 270), (1500, 420)),
    "substance_1": ((40, 425), (595, 1180)),
    "substance_2": ((605, 425), (1220, 1180)),
    "key_metrics": ((1225, 425), (1740, 1180)),
}

# --- PATHS ---
CHUNKS_JSONL = "data/chunks/merged_chunks.jsonl"
EMBEDDINGS_JSONL = "data/embeddings.jsonl"
FAISS_INDEX = "data/faiss_index.faiss"
LOG_PATH = "logs/QA.log"

# --- Setup ---
load_dotenv()
logging.basicConfig(level=logging.INFO, format="🔹 [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)
os.makedirs(os.path.dirname(CHUNKS_JSONL), exist_ok=True)
os.makedirs(os.path.dirname(EMBEDDINGS_JSONL), exist_ok=True)
os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)

# --- OpenAI client ---
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def run_chunking(pdf_path: str, pages: list[int], coords: dict) -> list[dict]:
    """
    Use your template-based chunker to extract JSON-like chunks from the PDF.
    Returns the in-memory list of chunk dicts.
    """
    logger.info("🚧 Chunking PDF...")
    chunks = extract_chunks_by_template(pdf_path, pages, coords)
    # persist to disk for record
    with open(CHUNKS_JSONL, "w", encoding="utf-8") as f:
        for chunk in chunks:
            f.write(json.dumps(chunk, ensure_ascii=False) + "\n")
    logger.info(f"✅ Wrote {len(chunks)} chunks to {CHUNKS_JSONL}")
    return chunks


def run_embedding(chunks: list[dict]) -> None:
    """
    Embed the provided chunks and save embeddings.jsonl.
    """
    logger.info("🚀 Embedding chunks...")
    vectors = embed_chunks(chunks)
    save_embeddings(vectors, EMBEDDINGS_JSONL)


def run_index_build() -> tuple[faiss.IndexFlatIP, list[dict]]:
    """
    Load embeddings.jsonl, build & save a FAISS index + metadata,
    then return the loaded index and metadata list.
    """
    logger.info("⚙️ Building FAISS index from embeddings...")
    idx, _ = build_and_save()  # assumes build_and_save reads EMBEDDINGS_JSONL
    return idx


def run_pipeline():
    """
    Full pipeline: chunk → embed → index → interactive Q&A.
    """
    # 1) Chunk
    chunks = run_chunking(PDF_PATH, PAGES_TO_USE, SECTION_COORDINATES_DICT)
    # 2) Embed
    run_embedding(chunks)
    # 3) Build & load index
    index = run_index_build()
    # 4) Enter QA loop
    interactive_qa_loop(chunks, index)  # ✅ doğru isim ve parametreler


if __name__ == "__main__":
    run_pipeline()
