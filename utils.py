import re


def clean_text(text: str) -> str:
    """Remove excessive whitespace and newlines from the input text."""
    return re.sub(r"\s*\n\s*", " ", text).strip()


def is_wide_block(block, page_width):
    """Check if the block spans more than 70% of the page width."""
    x0, y0, x1, y1 = block[:4]
    return (x1 - x0) > 0.7 * page_width


def is_bottom_block(block, page_height):
    """Determine whether the block is located near the bottom of the page."""
    y0 = block[1]
    return y0 > 0.7 * page_height


def extract_section(SECTION_HEADERS, header, all_blocks, content_blocks=None):
    """
    Extract content of a specific section starting from its header
    until the next header appears.
    """
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

    return " ".join(content).strip() if content else None


def detect_impact_layout_type(layout_blocks):
    """
    Determine which layout style is used for the 'Impact' section:
    bottom block, inline (middle), or first column.
    """
    if len(layout_blocks["bottom_full"]) >= 1:
        return "bottom_block", layout_blocks["bottom_full"]
    elif any("Impact" in b[4] for b in layout_blocks["col_2"] + layout_blocks["col_3"]):
        return "inline_block", layout_blocks["col_2"] + layout_blocks["col_3"]
    else:
        return "col_1_block", layout_blocks["col_1"]


def extract_highlight_metrics(page):
    """Extract prominent bold metrics in the 'Impact' section, based on font size and style."""
    metrics_found = set()
    page_dict = page.get_text("dict")

    for block in page_dict["blocks"]:
        if block.get("type") != 0:
            continue
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                text = span.get("text", "").strip()
                size = span.get("size", 0)
                font = span.get("font", "")
                color = span.get("color", -1)

                if not text:
                    continue

                # 🔥 Yeni kriter: Arial-BoldMT, font size 16–18, siyah (color=0)
                if font == "Arial-BoldMT" and 16.0 <= size <= 20.0 and color == 0:
                    metrics_found.add(text)

    return metrics_found


def analyze_global_metrics(page, page_label):
    """Print bold texts that may represent key metrics for manual inspection."""
    important_metrics = []
    page_dict = page.get_text("dict")

    for block in page_dict["blocks"]:
        if block.get("type") != 0:
            continue
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                font = span.get("font", "")
                size = span.get("size", 0)
                color = span.get("color", -1)
                text = span.get("text", "").strip()

                if (
                    font == "Arial-BoldMT"
                    and 16.0 <= size <= 20.0
                    and color == 0
                    and text
                ):
                    important_metrics.append(text)

    if important_metrics:
        print(f"📄 Sayfa {page_label}:\n📌 Bold metinler (önemli metrikler olabilir):")
        for metric in important_metrics:
            print(f"→ {metric}")
        print("")  # boşluk


def extract_impact_notes(impact_region):
    """Extract small-font note texts under the 'Impact' section."""
    return [clean_text(b[4]) for b in impact_region if b[5] < 9 and len(b[4]) > 20]
