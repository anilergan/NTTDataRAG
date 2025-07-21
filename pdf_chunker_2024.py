import fitz  # PyMuPDF
import json
import re
from utils import extract_section, detect_impact_layout_type, extract_highlight_metrics, analyze_global_metrics, extract_impact_notes, clean_text, is_wide_block, is_bottom_block

# === STATIC VARIABLES ===
PDF_PATH = r"data\raw\sr_2024_cb_v.pdf"
OUTPUT_PATH = "data\chunks_2024.jsonl"
INCLUDED_PAGES = [page for page in range(7, 24)] +\
                 [page for page in range(25, 35)] +\
                 [36, 37] +\
                 [page for page in range(39, 42)] +\
                 [44] +\
                 [page for page in range(46, 50)]
PAGE_OFFSET = 1

SECTION_HEADERS = ["Social issues", "Business need", "Solution", "Impact"]
HIGHLIGHT_SIZE_THRESHOLD = 15

def classify_layout_blocks(text_blocks, page_width, page_height):
    """Classify text blocks into layout regions: top header, columns, and bottom."""
    layout_blocks = {
        "full_width_top": [],
        "col_1": [],
        "col_2": [],
        "col_3": [],
        "bottom_full": []
    }
    for block in text_blocks:
        x0, y0, x1, y1, *_ = block
        if y1 < 200:
            layout_blocks["full_width_top"].append(block)
        elif is_bottom_block(block, page_height) and is_wide_block(block, page_width):
            layout_blocks["bottom_full"].append(block)
        elif x1 < page_width / 3:
            layout_blocks["col_1"].append(block)
        elif x0 > page_width * 2 / 3:
            layout_blocks["col_3"].append(block)
        else:
            layout_blocks["col_2"].append(block)
    return layout_blocks

def extract_filtered_spans(SECTION_HEADERS, PAGE_OFFSET, page, included_pages, allowed_colors={0, 8421504}):
    """
    Filter spans from the page: remove headers, too small or large fonts, wrong colors, etc.
    Return usable text blocks with positional and font data.
    """
    text_blocks = []
    page_dict = page.get_text("dict")

    for block in page_dict["blocks"]:
        if block.get("type") != 0:
            continue
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                text = span["text"].strip()
                if not text:
                    continue

                y0 = span["bbox"][1]
                x0, y0, x1, y1 = span["bbox"]

                # Section başlıkları
                if text in SECTION_HEADERS and (page.number + PAGE_OFFSET) in included_pages:
                    text_blocks.append((x0, y0, x1, y1, text, span["size"]))
                    continue

                # Sayfa başlığı veya alt başlığı
                if y0 < 100:
                    text_blocks.append((x0, y0, x1, y1, text, span["size"]))
                    continue

                # İçerik için filtre
                if span.get("color") not in allowed_colors:
                    continue
                if span.get("size", 0) < 6 or span.get("size", 0) > 25:
                    continue
                if len(text.split()) < 2:
                    continue

                text_blocks.append((x0, y0, x1, y1, text, span["size"]))
    return text_blocks

def extract_titles(top_blocks):
    """Identify and extract the main title and subtitle from the top blocks of the page."""
    if not top_blocks:
        return "", ""
    sorted_blocks = sorted(top_blocks, key=lambda b: (-b[5], b[1]))
    title_font = sorted_blocks[0][5]
    title_block = next((b for b in sorted_blocks if b[5] == title_font), None)
    subtitle_block = next((b for b in sorted_blocks if b[5] < title_font), None)
    return clean_text(title_block[4]) if title_block else "", clean_text(subtitle_block[4]) if subtitle_block else ""

def extract_chunks(pdf_path, included_pages):
    """Main logic to extract and structure chunks from relevant pages in a given PDF. Processes all headers and their associated contents."""
    doc = fitz.open(pdf_path)
    all_chunks = []

    for page in doc:
        page_label = page.number + PAGE_OFFSET
        if page_label not in included_pages:
            continue

        text_blocks = extract_filtered_spans(page, included_pages)
        text_blocks = sorted(text_blocks, key=lambda b: (b[1], b[0]))
        page_width, page_height = page.rect.width, page.rect.height
        layout_blocks = classify_layout_blocks(text_blocks, page_width, page_height)

        # Başlıkları ayıkla
        page_title, page_subtitle = extract_titles(layout_blocks["full_width_top"])

        all_blocks = (
            layout_blocks["full_width_top"]
            + layout_blocks["col_1"]
            + layout_blocks["col_2"]
            + layout_blocks["col_3"]
            + layout_blocks["bottom_full"]
        )

        # Section Extraction
        social_text = extract_section("Social issues", all_blocks, layout_blocks["full_width_top"])
        business_text = extract_section("Business need", all_blocks, layout_blocks["col_1"])
        solution_text = extract_section("Solution", all_blocks, layout_blocks["col_2"] + layout_blocks["col_3"])

        # === Impact ===
        layout_type, impact_blocks = detect_impact_layout_type(layout_blocks)
        impact_text = extract_section("Impact", all_blocks, impact_blocks)
        impact_region = impact_blocks

        # Font analizini yap ve bastır
        analyze_global_metrics(page, page_label)
        # Öne çıkan metrik ve notları ayıkla
        highlight_texts = extract_highlight_metrics(page)
        note_blocks = extract_impact_notes(impact_region)

        # Final impact zenginleştirme
        if impact_text:
            if highlight_texts:
                impact_text += f" (highlighted: {', '.join(highlight_texts)})"
            if note_blocks:
                impact_text += f" [note: {' '.join(note_blocks)}]"

        # Chunk oluştur
        for header, content in [
            ("Social issues", social_text),
            ("Business need", business_text),
            ("Solution", solution_text),
            ("Impact", impact_text)
        ]:
            if content:
                all_chunks.append({
                    "main_title_of_page": page_title,
                    "main_subtitle_of_page": page_subtitle,
                    "header": header,
                    "content": content,
                    "page": page_label,
                    "source": "sr_2024_cb_v.pdf"
                })

    return all_chunks


# === Ana Çalıştırıcı ===
if __name__ == "__main__":
    chunks = extract_chunks(PDF_PATH, INCLUDED_PAGES)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        for chunk in chunks:
            f.write(json.dumps(chunk, ensure_ascii=False) + "\n")
    print(f"✅ {len(chunks)} chunks extracted → {OUTPUT_PATH}")
