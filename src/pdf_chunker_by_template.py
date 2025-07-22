import json
import os

import fitz  # PyMuPDF

from config import (
    PAGES_TO_USE_PDF_2022,
    PAGES_TO_USE_PDF_2023,
    SECTION_COORDINATES_DICT_PDF_2022,
    SECTION_COORDINATES_DICT_PDF_2023,
)
from logger import logger


def extract_chunks_by_template(
    pdf_path: str,
    pages: list[int],
    section_coordinates_dict: dict[
        str, tuple[tuple[float, float], tuple[float, float]]
    ],
) -> list[dict]:
    """
    Extracts chunks from the given PDF according to fixed rectangular regions.
    """
    try:
        doc = fitz.open(pdf_path)
        logger.info(f"Opened PDF `{pdf_path}` ({doc.page_count} pages).")
    except Exception as e:
        logger.exception(f"Failed to open PDF `{pdf_path}`: {e}")
        return []

    page_count = doc.page_count
    source = os.path.basename(pdf_path)
    basename = source.rsplit(".", 1)[0] + ".pdf"
    chunks: list[dict] = []

    for page_num in pages:
        if not (1 <= page_num <= page_count):
            logger.warning(f"Skipping page {page_num}: out of range (1–{page_count})")
            continue

        try:
            logger.info(f"Processing page {page_num}...")
            page = doc[page_num - 1]
            page_dict = page.get_text("dict")

            # her sayfa için başlat
            section_spans = {name: [] for name in section_coordinates_dict}

            # 1) span’ları toplama
            for block in page_dict["blocks"]:
                if block.get("type") != 0:
                    continue
                for line in block["lines"]:
                    for sp in line["spans"]:
                        text = sp["text"].strip()
                        if not text:
                            continue
                        x0, y0, x1, y1 = sp["bbox"]
                        sz = sp.get("size", 0)
                        col = sp.get("color", 0)

                        # 2) intersection kontrolü
                        for name, (
                            (sx0, sy0),
                            (sx1, sy1),
                        ) in section_coordinates_dict.items():
                            if x1 > sx0 and x0 < sx1 and y1 > sy0 and y0 < sy1:
                                section_spans[name].append((text, sz, col, x0, y0))
                                logger.debug(
                                    f"[{page_num}:{name}] {text!r} @ ({x0:.1f},{y0:.1f}) size={sz} col={col}"
                                )

            # 3) title & subtitle
            title_list = section_spans.get("main_title_of_page", [])
            title = title_list[0][0] if title_list else ""
            if title:
                logger.info(f"[Page {page_num}] Detected title: {title!r}")
            subtitle_list = section_spans.get("main_subtitle_of_page", [])
            subtitle = " ".join(
                text for text, *_ in sorted(subtitle_list, key=lambda t: (t[4], t[3]))
            )
            if subtitle:
                logger.info(f"[Page {page_num}] Detected subtitle: {subtitle!r}")

            # 4) dynamic headers
            for header_key, spans in section_spans.items():
                if header_key in (
                    "main_title_of_page",
                    "main_subtitle_of_page",
                    "substance_1",
                    "substance_2",
                ):
                    continue
                content = " ".join(
                    text for text, *_ in sorted(spans, key=lambda t: (t[4], t[3]))
                )
                header_name = header_key.replace("_", " ").title()
                chunks.append(
                    {
                        "main_title_of_page": title,
                        "main_subtitle_of_page": subtitle,
                        "header": header_name,
                        "content": content,
                        "page": page_num,
                        "source": basename,
                    }
                )
                logger.info(
                    f"[Page {page_num}] Chunk `{header_name}` with {len(spans)} spans"
                )

            # 5) substance özel birleştirme
            if "substance_1" in section_spans:
                s1 = section_spans["substance_1"]
                s2 = section_spans.get("substance_2", [])
                substance = ""
                if s1:
                    _, ref_sz, ref_col, _, _ = s1[0]
                    merged = s1 + s2
                    filtered = [
                        (text, x0, y0)
                        for text, sz, col, x0, y0 in merged
                        if sz == ref_sz and col == ref_col
                    ]
                    substance = " ".join(
                        text
                        for text, *_ in sorted(filtered, key=lambda t: (t[2], t[1]))
                    )
                chunks.append(
                    {
                        "main_title_of_page": title,
                        "main_subtitle_of_page": subtitle,
                        "header": "Substance",
                        "content": substance,
                        "page": page_num,
                        "source": basename,
                    }
                )
                logger.info(
                    f"[Page {page_num}] Chunk `Substance` with {len(filtered) if s1 else 0} spans"
                )

            # 6) Key Metrics
            klist = section_spans.get("key_metrics", [])
            merged_texts: list[str] = []
            for text, sz, col, x0, y0 in sorted(klist, key=lambda t: (t[4], t[3])):
                lower = text.lower()
                if (
                    "click here for reference article" in lower
                    or "click here for the reference video" in lower
                ):
                    logger.debug(f"Excluding reference link span: {text!r}")
                    continue
                merged_texts.append(text)
            key_metrics = " ".join(merged_texts)
            chunks.append(
                {
                    "main_title_of_page": title,
                    "main_subtitle_of_page": subtitle,
                    "header": "Key Metrics",
                    "content": key_metrics,
                    "page": page_num,
                    "source": basename,
                }
            )
            logger.info(
                f"[Page {page_num}] Chunk `Key Metrics` with {len(merged_texts)} spans"
            )

        except Exception as e:
            logger.exception(f"Error processing page {page_num}: {e}")
            continue

    return chunks


def px2pt(coord, dpi=150):
    return tuple(c * 72 / dpi for c in coord)


def run_chunking_for_year(year: int, pdf_path: str, pages: list[int], coords_px: dict):
    logger.info(f"=== Starting chunking for {year} ===")
    try:
        # px → pt
        coords_pt = {key: (px2pt(tl), px2pt(br)) for key, (tl, br) in coords_px.items()}
        chunks = extract_chunks_by_template(pdf_path, pages, coords_pt)

        output_file = f"data/chunks/chunks_pdf_{year}.jsonl"
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as f:
            for c in chunks:
                f.write(json.dumps(c, ensure_ascii=False) + "\n")

        logger.info(f"✅ {len(chunks)} chunks written to {output_file}")
    except Exception as e:
        logger.exception(f"Failed to chunk PDF for {year}: {e}")


if __name__ == "__main__":
    run_chunking_for_year(
        year=2022,
        pdf_path="data/raw/sr_2022_cb_v_split.pdf",
        pages=PAGES_TO_USE_PDF_2022,
        coords_px=SECTION_COORDINATES_DICT_PDF_2022,
    )
    run_chunking_for_year(
        year=2023,
        pdf_path="data/raw/sr_2023_cb_v.pdf",
        pages=PAGES_TO_USE_PDF_2023,
        coords_px=SECTION_COORDINATES_DICT_PDF_2023,
    )
