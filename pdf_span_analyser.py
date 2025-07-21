import fitz  # PyMuPDF


def print_page_spans(pdf_path: str, page_number: int):
    """
    Belirtilen sayfadaki tüm yazıları yukarıdan aşağıya sıralı şekilde yazdırır.
    Her yazı için font, boyut, renk ve pozisyon gibi bilgiler gösterilir.
    """
    doc = fitz.open(pdf_path)

    if page_number < 0 or page_number >= len(doc):
        print(f"⚠️ Sayfa numarası geçersiz. PDF {len(doc)} sayfa içeriyor.")
        return

    page = doc[page_number]
    page_dict = page.get_text("dict")

    span_list = []

    for block in page_dict["blocks"]:
        if block.get("type") != 0:  # sadece metin blokları
            continue
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                text = span["text"].strip()
                if not text:
                    continue

                span_list.append(
                    {
                        "y": span["bbox"][1],  # yukarıdan aşağı sıralamak için
                        "text": text,
                        "font": span["font"],
                        "size": span["size"],
                        "color": span["color"],
                        "bbox": span["bbox"],
                    }
                )

    # Y koordinatına göre sıralıyoruz (yukarıdan aşağıya)
    span_list.sort(key=lambda s: s["y"])

    # Yazdır
    print(f"\n📄 PDF: {pdf_path} | Sayfa: {page_number}\n")
    for i, span in enumerate(span_list):
        print(f'{i + 1:02d}. "{span["text"]}"')
        print(
            f"    • Font: {span['font']} | Size: {span['size']} | Color: {span['color']}"
        )
        print(f"    • BBox: {span['bbox']}")
        print("-" * 60)


if __name__ == "__main__":
    PDF_PATH = r"data\raw\sr_2020_cb_p.pdf"
    print_page_spans(PDF_PATH, page_number=8)
