import fitz  # PyMuPDF
import json
import re
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer, LTChar

# === Ayarlar ===
PDF_PATH = r"data\raw\sr_2024_cb_v.pdf"
OUTPUT_PATH = "data\chunks.jsonl"
INCLUDED_PAGES = [page for page in range(7, 24)] +\
                 [page for page in range(25, 35)] +\
                 [36, 37] +\
                 [page for page in range(39, 42)] +\
                 [44] +\
                 [page for page in range(46, 50)]
PAGE_OFFSET = 1

SECTION_HEADERS = ["Social issues", "Business need", "Solution", "Impact"]
HIGHLIGHT_SIZE_THRESHOLD = 15

def clean_text(text: str) -> str:
    return re.sub(r'\s*\n\s*', ' ', text).strip()

def is_wide_block(block, page_width):
    x0, y0, x1, y1 = block[:4]
    return (x1 - x0) > 0.7 * page_width

def is_bottom_block(block, page_height):
    y0 = block[1]
    return y0 > 0.7 * page_height

def classify_layout_blocks(text_blocks, page_width, page_height):
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


def extract_section(header, all_blocks, content_blocks=None):
    content = []
    found = False
    if content_blocks is None:
        content_blocks = all_blocks

    for block in all_blocks:
        text = clean_text(block[4])
        if not text:
            continue
        if text.strip() == header:
            found = True
            continue
        if found and text in SECTION_HEADERS:
            break
        if found and block in content_blocks:
            content.append(text)

    return ' '.join(content).strip() if content else None

def extract_filtered_spans(page, included_pages, allowed_colors={0, 8421504}):
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

def extract_chunks(pdf_path, included_pages):
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

        # Başlıklar
        top_blocks = layout_blocks["full_width_top"]
        page_title = page_subtitle = ""
        if top_blocks:
            top_blocks_sorted = sorted(top_blocks, key=lambda b: (-b[5], b[1]))
            title_font = top_blocks_sorted[0][5]
            title_block = next((b for b in top_blocks_sorted if b[5] == title_font), None)
            page_title = clean_text(title_block[4]) if title_block else ""
            subtitle_block = next((b for b in top_blocks_sorted if b[5] < title_font), None)
            page_subtitle = clean_text(subtitle_block[4]) if subtitle_block else ""

        def create_chunk(header, content):
            if content:
                return {
                    "main_title_of_page": page_title,
                    "main_subtitle_of_page": page_subtitle,
                    "header": header,
                    "content": content,
                    "page": page_label,
                    "source": "sr_2024_cb_v.pdf"
                }

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

        # Impact Section
        impact_text_col1 = extract_section("Impact", all_blocks, layout_blocks["col_1"])
        impact_text_bottom = extract_section("Impact", all_blocks, layout_blocks["bottom_full"])
        final_impact = impact_text_col1 or impact_text_bottom
        impact_region = layout_blocks["col_1"] if impact_text_col1 else layout_blocks["bottom_full"]

        # 🔥 Nokta atışı metrik tespiti — sayısal, zamansal, oransal ifadeler (tüm sayfada)
        highlight_texts = []
        for b in text_blocks:
            text = clean_text(b[4])
            size = b[5]

            if not text or not isinstance(text, str):
                continue

            if size >= 13 and re.search(r"(approx|%|year|month|employees|rate|reduction|increase|minimum|as of)", text.lower()):
                highlight_texts.append(text)

        # Dipnotlar
        note_blocks = [
            clean_text(b[4]) for b in impact_region
            if b[5] < 9 and len(b[4]) > 20
        ]

        # Final impact'e highlight + note ekle
        if final_impact:
            if highlight_texts:
                final_impact += f" (highlighted: {', '.join(highlight_texts)})"
            if note_blocks:
                final_impact += f" [note: {' '.join(note_blocks)}]"

        # Chunk Ekleme
        for header, content in [
            ("Social issues", social_text),
            ("Business need", business_text),
            ("Solution", solution_text),
            ("Impact", final_impact)
        ]:
            chunk = create_chunk(header, content)
            if chunk:
                all_chunks.append(chunk)

    return all_chunks



# === Ana Çalıştırıcı ===
if __name__ == "__main__":
    chunks = extract_chunks(PDF_PATH, INCLUDED_PAGES)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        for chunk in chunks:
            f.write(json.dumps(chunk, ensure_ascii=False) + "\n")
    print(f"✅ {len(chunks)} chunks extracted → {OUTPUT_PATH}")
