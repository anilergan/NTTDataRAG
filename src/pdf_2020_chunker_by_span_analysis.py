import json

import fitz  # PyMuPDF

from config import PAGES_TO_USE_PDF_2020
from logger import logger

"""
Filter for sr_2020_cv_p.pdf

main_title_of_page: 
- font size: 23.5 < x < 25
- color: 2301728 

main_subtitle_of_page:
- font size 8.5 < x < 9.5
- color: 6995151

key-metrics 
- font size x > 16
- color: 6995151 

- substance
- size 8.5 < x < 9.5
- color: 2301728
- font must be DINNextLTPro-Medium
- page must be suplitted:

    -> BBox's first element is 70.86620330810547 for left part substance.
    -> So If it's smaller then 200 it's left part text and it must be reached first.

    -> BBox' first element is 311.814208984375 for right part substance
    -> So if it's bigger then 200 it's right part text and it must be reached after left part done.
"""


def extract_chunks(pdf_path: str, page_numbers: list[int], output_path: str):
    try:
        doc = fitz.open(pdf_path)
        logger.info(f"Opened PDF: {pdf_path} with {len(doc)} pages.")
    except Exception as e:
        logger.error(f"❌ Failed to open PDF: {e}")
        return

    chunks = []

    for real_page_num in page_numbers:
        page_index = real_page_num - 1
        if page_index < 0 or page_index >= len(doc):
            logger.warning(f"⚠️ Skipping invalid page number: {real_page_num}")
            continue

        try:
            logger.info(f"🔍 Processing page {real_page_num}...")

            page = doc[page_index]
            page_dict = page.get_text("dict")

            main_title = ""
            main_subtitle = ""
            key_metrics = []
            substance_left = []
            substance_right = []

            for block in page_dict["blocks"]:
                if block["type"] != 0:
                    continue
                for line in block["lines"]:
                    for span in line["spans"]:
                        text = span["text"].strip()
                        size = span["size"]
                        color = span["color"]
                        font_fam = span["font"]
                        x0 = span["bbox"][0]

                        if 23.5 < size < 25.0 and color == 2301728:
                            main_title += text + " "
                        elif 8.5 < size < 9.5 and color == 6995151:
                            main_subtitle += text + " "
                        elif size > 16 and color == 6995151:
                            key_metrics.append(text)
                        elif (
                            8.5 < size < 9.5
                            and color == 2301728
                            and "DINNextLTPro" in font_fam
                        ):
                            if x0 < 200:
                                substance_left.append(text)
                            else:
                                substance_right.append(text)

            # Temizle
            main_title = main_title.strip()
            main_subtitle = main_subtitle.strip()
            substance_text = " ".join(substance_left + substance_right).strip()
            key_metric_text = " ".join(key_metrics).strip()

            if key_metric_text:
                chunks.append(
                    {
                        "main_title_of_page": main_title,
                        "main_subtitle_of_page": main_subtitle,
                        "header": "Key-Metrics",
                        "content": key_metric_text,
                        "page": real_page_num,
                        "source": pdf_path.split("/")[-1],
                    }
                )

            if substance_text:
                chunks.append(
                    {
                        "main_title_of_page": main_title,
                        "main_subtitle_of_page": main_subtitle,
                        "header": "Substance",
                        "content": substance_text,
                        "page": real_page_num,
                        "source": pdf_path.split("/")[-1],
                    }
                )

            logger.info(
                f"✅ Page {real_page_num} → {bool(key_metric_text)} key-metrics, {bool(substance_text)} substance"
            )

        except Exception as e:
            logger.exception(f"❌ Error while processing page {real_page_num}: {e}")
            continue

    try:
        with open(output_path, "w", encoding="utf-8") as f:
            for chunk in chunks:
                f.write(json.dumps(chunk, ensure_ascii=False) + "\n")
        logger.info(f"📄 {len(chunks)} chunks written to {output_path}")
    except Exception as e:
        logger.error(f"❌ Failed to write output file: {e}")


if __name__ == "__main__":
    extract_chunks(
        pdf_path=r"data\raw\sr_2020_cb_p.pdf",
        page_numbers=PAGES_TO_USE_PDF_2020,
        output_path="data/chunks/chunks_pdf_2020.jsonl",
    )
