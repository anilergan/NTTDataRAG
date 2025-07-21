import fitz  # PyMuPDF
import json
from utils import (
    clean_text,
    analyze_global_metrics
)

PDF_PATH = r"data/raw/sr_2023_cb_v.pdf"
OUTPUT_PATH = "data/chunks_2023.jsonl"
INCLUDED_PAGES = [6]
PAGE_OFFSET = 1


def extract_titles(page):
    """
    Extract main_title and main_subtitle from entire page.
    - main_title: first span with Arial-BoldMT, 15.5 <= size <= 16.5, color != 0
    - main_subtitle: all spans with Arial-BoldMT, size == 20.0, color == 0
    """
    page_dict = page.get_text("dict")
    main_title = ""
    main_title_color = None
    subtitle_parts = []

    for block in page_dict.get("blocks", []):
        if block.get("type") != 0:
            continue
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                text = span.get("text", "").strip()
                font = span.get("font", "")
                size = span.get("size", 0)
                color = span.get("color", 0)

                if not text:
                    continue

                # main_title → Arial-BoldMT, 15.5 ≤ size ≤ 16.5, color != 0
                if not main_title and font == "Arial-BoldMT" and 15.5 <= size <= 16.5 and color != 0:
                    main_title = text
                    main_title_color = color

                # main_subtitle → Arial-BoldMT, size == 20.0, color == 0
                if font == "Arial-BoldMT" and 19.5 <= size <= 20.5 and color == 0:
                    subtitle_parts.append(text)

    return main_title.strip(), " ".join(subtitle_parts).strip(), main_title_color




def classify_layout_blocks_3col(text_blocks, page_width, page_height):
    """
    Divide the page into 3 vertical columns plus 'top' area.
    """
    layout = {"col_1": [], "col_2": [], "col_3": [], "top": []}
    for x0, y0, x1, y1, txt, sz in text_blocks:
        if y1 < 140:
            layout["top"].append((x0, y0, x1, y1, txt, sz))
        elif x1 <= page_width / 3:
            layout["col_1"].append((x0, y0, x1, y1, txt, sz))
        elif x0 >= page_width * 2 / 3:
            layout["col_3"].append((x0, y0, x1, y1, txt, sz))
        else:
            layout["col_2"].append((x0, y0, x1, y1, txt, sz))
    return layout


def extract_filtered_spans(page):
    """
    Return all usable text spans (x0, y0, x1, y1, text, size),
    filtering out too-small, too-large, wrong-color or footnote spans.
    """
    blocks = []
    h = page.rect.height
    for b in page.get_text("dict")["blocks"]:
        if b.get("type") != 0:
            continue
        for line in b["lines"]:
            for s in line["spans"]:
                t = s["text"].strip()
                if not t:
                    continue
                x0, y0, x1, y1 = s["bbox"]
                sz = s.get("size", 0)
                col = s.get("color", 0)
                if sz < 6 or sz > 25 or col not in {0, 8421504}:
                    continue
                if y0 > h - 80:  # dipnot/alt caption filtresi
                    continue
                blocks.append((x0, y0, x1, y1, t, sz))
    return blocks


def extract_social_and_substance(page, col_blocks):
    """
    After SOCIAL ISSUES y0, collect all col_1+col_2 spans with enough length.
    """
    social_y0 = None
    prev_text = ""

    for block in page.get_text("dict")["blocks"]:
        if block.get("type") != 0:
            continue
        for line in block["lines"]:
            for span in line["spans"]:
                text = span.get("text", "").strip()
                if not text:
                    continue

                combined = (prev_text + " " + text).strip().upper()
                if "SOCIAL ISSUES" in combined:
                    social_y0 = span["bbox"][1]
                    break

                prev_text = text
            if social_y0:
                break
        if social_y0:
            break

    if social_y0 is None:
        return ""

    paragraphs = []
    for x0, y0, x1, y1, t, sz in sorted(col_blocks, key=lambda b: (b[1], b[0])):
        if y0 <= social_y0:
            continue
        clean = clean_text(t)
        if len(clean) > 20:
            paragraphs.append(clean)

    return " ".join(paragraphs).strip()

def extract_key_metrics_with_color(page, title_text, title_color):
    """
    Find all spans with color similar to title_color (±100),
    excluding those that match title_text or 'SOCIAL ISSUES'.
    Return concatenated key metric text.
    """
    key_lines = []

    for b in page.get_text("dict")["blocks"]:
        if b.get("type") != 0:
            continue
        for ln in b["lines"]:
            for sp in ln["spans"]:
                text = sp.get("text", "").strip()
                if not text:
                    continue

                color = sp.get("color", -1)
                if abs(color - title_color) > 1:
                    continue

                # Skip title itself or "SOCIAL ISSUES"
                if text in title_text or "SOCIAL ISSUES" in text.upper() or "Carbon Neutrality" in text.upper():
                    continue

                key_lines.append(text)

    return " ".join(key_lines).strip()

def extract_text_in_bbox(page, bbox, color_filter=None, min_size=0):
    """
    Extract text from a page inside a bounding box (bbox).
    bbox = (x0, y0, x1, y1)
    Optionally filter by color and minimum size.
    """
    texts = []
    for b in page.get_text("dict")["blocks"]:
        if b.get("type") != 0:
            continue
        for ln in b["lines"]:
            for sp in ln["spans"]:
                x0, y0, x1, y1 = sp["bbox"]
                text = sp.get("text", "").strip()
                color = sp.get("color", 0)
                size = sp.get("size", 0)

                # Check if inside bbox
                if x0 >= bbox[0] and y0 >= bbox[1] and x1 <= bbox[2] and y1 <= bbox[3]:
                    if (color_filter is None or color == color_filter) and size >= min_size:
                        texts.append(text)
    return " ".join(texts).strip()

def extract_text_from_custom_area(page):
    """
    Extract and return plain text (no formatting) from the region:
    - right 1/3 horizontally
    - middle 1/3 vertically
    """
    width, height = page.rect.width, page.rect.height
    x_min = width * (2/3)
    x_max = width
    y_min = height * (1/3)
    y_max = height * (2/3)

    collected_text = []

    for block in page.get_text("dict")["blocks"]:
        if block.get("type") != 0:
            continue
        for line in block["lines"]:
            for span in line["spans"]:
                text = span.get("text", "").strip()
                if not text:
                    continue
                x0, y0, x1, y1 = span["bbox"]
                if x0 >= x_min and x1 <= x_max and y0 >= y_min and y1 <= y_max:
                    collected_text.append(text)

    return " ".join(collected_text)


def extract_chunks(pdf_path, included_pages):
    doc = fitz.open(pdf_path)
    chunks = []

    for page in doc:
        page_label = page.number + PAGE_OFFSET
        if page_label not in included_pages:
            continue
        text = extract_text_from_custom_area(page)
        print("\n📦 Extracted custom area text:\n", text)
        spans = extract_filtered_spans(page)
        print(f"\n— Processing page {page_label} —")
        print(f"Total spans after filter: {len(spans)}")

        # Sayfa yapısı ve başlıklar
        w, h = page.rect.width, page.rect.height
        layout = classify_layout_blocks_3col(spans, w, h)
        title, subtitle, title_color = extract_titles(page)
        print(f"Detected title:    '{title}'")
        print(f"Detected subtitle: '{subtitle}'")
        print(f"Title color:       {title_color}")

        # 3) social + substance
        social = extract_social_and_substance(page, layout["col_1"] + layout["col_2"])
        print(f"Social text length: {len(social)} characters")

        # 4) key metrics
        keymet = extract_key_metrics_with_color(page, title, title_color)
        print(f"Key metrics length: {len(keymet)} characters")

        if keymet:
            chunks.append({
                "main_title_of_page": title,
                "main_subtitle_of_page": subtitle,
                "header": "Key Metrics",
                "content": keymet,
                "page": page_label,
                "source": "sr_2023_cb_v.pdf"
            })

        # 5) şimdi eğer hala 0 ise, geçici olarak şu çıktıyı gör:
        if not title or not social:
            print("🔥 WARNING: Title or Social Issues is empty—check your filters!")

        # 6) chunks üretimi
        for hdr, cnt in [("Social Issues", social), ("Key Metrics", keymet)]:
            if cnt:
                chunks.append({
                    "main_title_of_page": title,
                    "main_subtitle_of_page": subtitle,
                    "header": hdr,
                    "content": cnt,
                    "page": page_label,
                    "source": "sr_2023_cb_v.pdf"
                })

    return chunks



if __name__ == "__main__":
    out = extract_chunks(PDF_PATH, INCLUDED_PAGES)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        for c in out:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
    print(f"✅ {len(out)} chunks extracted → {OUTPUT_PATH}")
