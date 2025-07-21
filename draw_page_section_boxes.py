import os

import fitz  # PyMuPDF
from PIL import Image, ImageDraw, ImageFont

from config import SECTION_COORDINATES_DICT_PDF_2022, SECTION_COORDINATES_DICT_PDF_2023


def draw_section_boxes_on_pdf_page(pdf_path, page_index, section_coordinates_dict):
    """
    section_coordinates_dict = {
        "social_issues": ((x0, y0), (x1, y1)),
        ...
    }
    """
    # 🎨 Pastel renkler (RGB) — 8 adet
    pastel_colors = [
        (35, 87, 188),
        (251, 180, 15),
        (213, 33, 39),
        (47, 187, 179),
        (115, 59, 151),
        (7, 177, 81),
        (243, 102, 33),
        (76, 72, 155),
    ]

    doc = fitz.open(pdf_path)
    page = doc[page_index - 1]

    # PDF sayfasını görüntü olarak al
    pix = page.get_pixmap(dpi=150)
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    draw = ImageDraw.Draw(img, "RGBA")

    font_size = 24
    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except:
        font = ImageFont.load_default()

    # Kutuları çiz
    for idx, (section_name, (top_left, bottom_right)) in enumerate(
        section_coordinates_dict.items()
    ):
        x0, y0 = top_left
        x1, y1 = bottom_right

        color = pastel_colors[idx % len(pastel_colors)]
        fill_color = (*color, 25)  # %10 opacity
        border_color = (*color, 255)

        # Dikdörtgen çiz (dolgu + border)
        draw.rectangle([x0, y0, x1, y1], fill=fill_color, outline=border_color, width=3)

        # Etiketi üst sol köşeye yaz (kutu dışında)
        label_pos = (x0, max(0, y0 - font_size - 4))
        draw.text(label_pos, section_name, fill=border_color, font=font)

    # ✅ Dosya adını otomatik belirle
    base_filename = os.path.basename(pdf_path).replace(".pdf", "")
    output_path = f"section_boxes/{base_filename}_page{page_index}_sections.jpg"
    img.save(output_path)
    print(f"✅ Saved marked page to: {output_path}")


if __name__ == "__main__":
    draw_section_boxes_on_pdf_page(
        pdf_path=r"data\raw\sr_2023_cb_v.pdf",
        page_index=17,
        section_coordinates_dict=SECTION_COORDINATES_DICT_PDF_2023,
    )
