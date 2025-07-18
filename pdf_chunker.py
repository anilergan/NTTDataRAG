# pdf_chunker.py
import os
import json
import fitz  # PyMuPDF
import re
import unicodedata

DATA_DIR = "data"
RAW_DATA_DIR = "data/raw"
CHUNK_OUTPUT_PATH = os.path.join(DATA_DIR, "chunks.jsonl")
CHUNK_SIZE = 1200
OVERLAP = 200

def clean_text(text: str) -> str:
    # Unicode normalization
    text = unicodedata.normalize("NFKC", text)

    # Invisible characters & weird unicode artifacts
    text = text.replace("\u200b", "").replace("\xa0", " ")

    # Remove control characters
    text = ''.join(ch for ch in text if ch.isprintable())

    # Remove multiple spaces and newlines
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n", "\n", text).strip()

    return text

def extract_blocks_ordered(page: fitz.Page) -> str:
    """
    Sayfa içindeki text bloklarını (bbox, text) alır,
    yukarıdan aşağı → soldan sağ sıralar ve tek string döner.
    """
    blocks = page.get_text("blocks")
    # blocks: (x0, y0, x1, y1, "text", block_no, block_type)
    blocks = sorted(
        [b for b in blocks if b[4].strip()],
        key=lambda b: (round(b[1], 1), round(b[0], 1))
    )
    ordered_text = "\n".join(b[4].strip() for b in blocks)
    return ordered_text


def extract_chunks_from_pdf(pdf_path: str,
                            chunk_size: int = CHUNK_SIZE,
                            overlap: int = OVERLAP) -> list[dict]:
    """
    Bir PDF dosyasını okuyup blok sıralı metni chunk'lara böler.
    """
    doc = fitz.open(pdf_path)
    chunks: list[dict] = []

    for page_idx, page in enumerate(doc):
        text = extract_blocks_ordered(page)
        text = clean_text(text)
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunk_text = text[start:end].strip()
            if chunk_text:
                chunks.append({
                    "source": os.path.basename(pdf_path),
                    "page": page_idx + 1,
                    "content": chunk_text
                })
            start = end - overlap  # overlap kadar geri kay

    doc.close()
    return chunks


def chunk_all_pdfs(data_dir: str = RAW_DATA_DIR) -> None:
    """
    data_dir altındaki tüm PDF’leri chunk'lar ve çıktıyı .jsonl olarak kaydeder.
    """
    all_chunks: list[dict] = []

    for fname in os.listdir(data_dir):
        if fname.lower().endswith(".pdf"):
            pdf_path = os.path.join(data_dir, fname)
            print(f"📄 Processing: {fname}")
            all_chunks.extend(extract_chunks_from_pdf(pdf_path))

    # JSON Lines dosyası olarak yaz
    with open(CHUNK_OUTPUT_PATH, "w", encoding="utf-8") as f:
        for chunk in all_chunks:
            f.write(json.dumps(chunk, ensure_ascii=False) + "\n")

    print(f"\n✅ {len(all_chunks)} chunks written to {CHUNK_OUTPUT_PATH}")


if __name__ == "__main__":
    chunk_all_pdfs()