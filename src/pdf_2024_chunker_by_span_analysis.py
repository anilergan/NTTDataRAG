import json
import os

import fitz  # PyMuPDF

from config import PAGES_TO_USE_PDF_2024
from logger import logger


def extract_chunks(pdf_path: str, pages: list[int], output_path: str) -> None:
    """
    Extracts chunks from the given PDF over the specified pages,
    using span-based y0/font/size/color filters, then writes to JSONL.
    """
    try:
        doc = fitz.open(pdf_path)
        logger.info(f"Opened PDF `{pdf_path}` ({doc.page_count} pages).")
    except Exception as e:
        logger.exception(f"❌ Failed to open PDF `{pdf_path}`: {e}")
        return

    all_chunks: list[dict] = []

    for page_num in pages:
        try:
            if not (1 <= page_num <= doc.page_count):
                logger.warning(f"Skipping invalid page {page_num} (out of range).")
                continue

            logger.info(f"🔍 Processing page {page_num}...")
            page = doc[page_num - 1]
            page_dict = page.get_text("dict")

            # 1) Collect spans
            spans: list[dict] = []
            for block in page_dict["blocks"]:
                if block.get("type") != 0:
                    continue
                for line in block["lines"]:
                    for sp in line["spans"]:
                        text = sp["text"].strip()
                        if not text:
                            continue
                        x0, y0, x1, y1 = sp["bbox"]
                        # y0 filtresi
                        if y0 < 55 or y0 > 520:
                            continue

                        span = {
                            "text": text,
                            "font": sp.get("font"),
                            "size": sp.get("size", 0),
                            "color": sp.get("color", 0),
                            "x0": x0,
                            "y0": y0,
                            "x1": x1,
                        }
                        spans.append(span)
                        logger.debug(
                            f"[{page_num}] Collected span: {text!r} @ y0={y0:.1f}"
                        )

            # 2) Titles
            title = " ".join(
                s["text"] for s in spans if 17 < s["size"] < 20 and s["y0"] < 70
            ).strip()
            subtitle = " ".join(
                s["text"] for s in spans if 13 < s["size"] < 15 and s["y0"] < 120
            ).strip()
            logger.info(f"[{page_num}] Title: {title!r}")
            logger.info(f"[{page_num}] Subtitle: {subtitle!r}")

            # 3) y0 refs
            impact_y0 = next(
                (s["y0"] for s in spans if s["text"].lower().startswith("impact")), None
            )
            business_y0 = next(
                (
                    s["y0"]
                    for s in spans
                    if s["text"].lower().startswith("business need")
                ),
                None,
            )
            if impact_y0 is None or business_y0 is None:
                logger.warning(
                    f"[{page_num}] Could not find both Business need y0 and Impact y0."
                )
                continue

            # 4) Social Issues
            social = " ".join(
                s["text"]
                for s in spans
                if s["y0"] < business_y0
                and 9 < s["size"] <= 10
                and abs(s["color"] - 0) < 100
            ).strip()
            all_chunks.append(
                {
                    "main_title_of_page": title,
                    "main_subtitle_of_page": subtitle,
                    "header": "Social Issues",
                    "content": social,
                    "page": page_num,
                    "source": os.path.basename(pdf_path),
                }
            )
            logger.info(
                f"[{page_num}] Chunk `Social Issues`: {len(social.split())} words"
            )

            # 5) Business need (sol sütun)
            business = " ".join(
                s["text"]
                for s in spans
                if business_y0 < s["y0"] < impact_y0
                and 8.5 < s["size"] < 9.5
                and abs(s["color"] - 0) < 100
                and s["x1"] < 280
            ).strip()
            all_chunks.append(
                {
                    "main_title_of_page": title,
                    "main_subtitle_of_page": subtitle,
                    "header": "Business need",
                    "content": business,
                    "page": page_num,
                    "source": os.path.basename(pdf_path),
                }
            )
            logger.info(
                f"[{page_num}] Chunk `Business need`: {len(business.split())} words"
            )

            # 6) Solution (orta + sağ sütun)
            sol_mid = [
                s["text"]
                for s in spans
                if business_y0 < s["y0"] < impact_y0
                and 8.5 < s["size"] < 9.5
                and abs(s["color"] - 0) < 100
                and 280 <= s["x1"] <= 545
            ]
            sol_rig = [
                s["text"]
                for s in spans
                if s["y0"] > business_y0
                and 8.5 < s["size"] < 9.5
                and abs(s["color"] - 0) < 100
                and s["x1"] > 545
                and s["y0"] < impact_y0
            ]
            solution = " ".join(sol_mid + sol_rig).strip()
            all_chunks.append(
                {
                    "main_title_of_page": title,
                    "main_subtitle_of_page": subtitle,
                    "header": "Solution",
                    "content": solution,
                    "page": page_num,
                    "source": os.path.basename(pdf_path),
                }
            )
            logger.info(f"[{page_num}] Chunk `Solution`: {len(solution.split())} words")

            # 7) Impact
            impact = " ".join(s["text"] for s in spans if s["y0"] > impact_y0).strip()
            all_chunks.append(
                {
                    "main_title_of_page": title,
                    "main_subtitle_of_page": subtitle,
                    "header": "Impact",
                    "content": impact,
                    "page": page_num,
                    "source": os.path.basename(pdf_path),
                }
            )
            logger.info(f"[{page_num}] Chunk `Impact`: {len(impact.split())} words")

        except Exception as e:
            logger.exception(f"❌ Error processing page {page_num}: {e}")
            continue

    # 8) Write output
    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            for chunk in all_chunks:
                f.write(json.dumps(chunk, ensure_ascii=False) + "\n")
        logger.info(f"✅ {len(all_chunks)} chunks written to {output_path}")
    except Exception as e:
        logger.exception(f"❌ Failed to write output file `{output_path}`: {e}")


if __name__ == "__main__":
    extract_chunks(
        pdf_path=r"data/raw/sr_2024_cb_v.pdf",
        pages=PAGES_TO_USE_PDF_2024,
        output_path="data/chunks/chunks_pdf_2024.jsonl",
    )
