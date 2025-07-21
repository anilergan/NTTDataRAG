import fitz  # PyMuPDF
import os
import json

def extract_chunks_by_template(
    pdf_path: str,
    pages: list[int],
    section_coordinates_dict: dict[str, tuple[tuple[float,float], tuple[float,float]]]
) -> list[dict]:
    """
    Extracts chunks from the given PDF according to fixed rectangular regions.
    """
    doc = fitz.open(pdf_path)
    page_count = doc.page_count
    source = os.path.basename(pdf_path)
    basename = source.rsplit(".", 1)[0] + ".pdf"
    chunks: list[dict] = []

    for page_num in pages:
        if not (1 <= page_num <= page_count):
            print(f"⚠️  Skipping page {page_num}: not in document (1–{page_count})")
            continue

        page_index = page_num - 1
        page = doc[page_index]
        page_dict = page.get_text("dict")

        # ————————————————
        # 📦 Her sayfa için sıfırdan oluştur:
        section_spans: dict[str, list[tuple[str,float,int,float,float]]] = {
            name: [] for name in section_coordinates_dict
        }

        # 1) Span’ları topla
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

                    # 2) Intersection (çakışma) mantığı
                    for name, ((sx0, sy0), (sx1, sy1)) in section_coordinates_dict.items():
                        if x1 > sx0 and x0 < sx1 and y1 > sy0 and y0 < sy1:
                            section_spans[name].append((text, sz, col, x0, y0))

        # ————————————————
        # 3) Titles
        title_list = section_spans["main_title_of_page"]
        if title_list:
            title, _, title_color, _, _ = title_list[0]
        else:
            title, title_color = "", None

        subtitle_list = section_spans["main_subtitle_of_page"]
        subtitle = " ".join(
            text for text, _, _, _, _ in
            sorted(subtitle_list, key=lambda t: (t[4], t[3]))
        )

        # 4) Social Issues
        social_list = section_spans["social_issues"]
        social = " ".join(
            text for text, _, _, _, _ in
            sorted(social_list, key=lambda t: (t[4], t[3]))
        )
        chunks.append({
            "main_title_of_page": title,
            "main_subtitle_of_page": subtitle,
            "header": "Social Issues",
            "content": social,
            "page": page_num,
            "source": basename
        })

        # 5) Substance (merge substance_1 + substance_2 with font/renk filter)
        s1 = section_spans["substance_1"]
        s2 = section_spans["substance_2"]
        substance = ""
        if s1:
            _, ref_size, ref_col, _, _ = s1[0]
            merged = s1 + s2
            filtered = [
                (text, x0, y0)
                for text, sz, col, x0, y0 in merged
                if sz == ref_size and col == ref_col
            ]
            substance = " ".join(
                text for text, x0, y0 in
                sorted(filtered, key=lambda t: (t[2], t[1]))
            )
        chunks.append({
            "main_title_of_page": title,
            "main_subtitle_of_page": subtitle,
            "header": "Substance",
            "content": substance,
            "page": page_num,
            "source": basename
        })

        # 6) Key Metrics (exclude reference links)
        klist = section_spans["key_metrics"]
        merged_texts: list[str] = []
        for text, sz, col, x0, y0 in sorted(klist, key=lambda t: (t[4], t[3])):
            lower = text.lower()
            if "click here for reference article" in lower or "click here for the reference video" in lower:
                continue
            merged_texts.append(text)
        key_metrics = " ".join(merged_texts)
        chunks.append({
            "main_title_of_page": title,
            "main_subtitle_of_page": subtitle,
            "header": "Key Metrics",
            "content": key_metrics,
            "page": page_num,
            "source": basename
        })

    return chunks

def px2pt(coord, dpi=150):
    return tuple(c * 72 / dpi for c in coord)

if __name__ == "__main__":
    section_coords_px = {
        "main_title_of_page": ((40, 115), (338, 270)),
        "main_subtitle_of_page": ((350, 115), (1500, 270)),
        "social_issues": ((250, 270), (1500, 420)),
        "substance_1": ((40, 425), (595, 1180)),
        "substance_2": ((605, 425), (1220, 1180)),
        "key_metrics": ((1225, 425), (1740, 1180)),
    }
    dpi = 150
    # 🔁 Hepsini px → pt çevir
    section_coords = {
        key: (px2pt(tl, dpi), px2pt(br, dpi))
        for key, (tl, br) in section_coords_px.items()
    }
    pdf_path = "data/raw/sr_2023_cb_v.pdf"
    pages = [10]  # örnek geçerli sayfa numarası
    chunks = extract_chunks_by_template(pdf_path, pages, section_coords)

    output_path = f"data/{os.path.basename(pdf_path).rsplit('.',1)[0]}_chunks.jsonl"
    with open(output_path, "w", encoding="utf-8") as f:
        for c in chunks:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")

    print(f"✅ {len(chunks)} chunks written to {output_path}")
