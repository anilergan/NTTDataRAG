import fitz  # PyMuPDF


def split_double_pages_vertically(pdf_path, output_path, avoid_pages=None):
    """
    Bir PDF'in içindeki sayfaları tam ortadan dikey olarak ikiye böler (soldaki ve sağdaki),
    avoid_pages içindekileri atlayarak yeni bir PDF oluşturur.

    :param pdf_path: Girdi PDF dosyasının yolu
    :param output_path: Çıktı PDF dosyasının yolu
    :param avoid_pages: Bölünmeyecek sayfa indeksleri (0'dan başlar)
    """
    if avoid_pages is None:
        avoid_pages = []

    input_pdf = fitz.open(pdf_path)
    output_pdf = fitz.open()

    for i, page in enumerate(input_pdf):
        if i in avoid_pages:
            output_pdf.insert_pdf(input_pdf, from_page=i, to_page=i)
            continue

        width = page.rect.width
        height = page.rect.height

        # Sol yarı
        left_rect = fitz.Rect(0, 0, width / 2, height)
        left_page = output_pdf.new_page(width=width / 2, height=height)
        left_page.show_pdf_page(left_page.rect, input_pdf, i, clip=left_rect)

        # Sağ yarı
        right_rect = fitz.Rect(width / 2, 0, width, height)
        right_page = output_pdf.new_page(width=width / 2, height=height)
        right_page.show_pdf_page(right_page.rect, input_pdf, i, clip=right_rect)

    output_pdf.save(output_path)
    output_pdf.close()
    input_pdf.close()


if __name__ == "__main__":
    split_double_pages_vertically(
        pdf_path=r"data\raw\sr_2022_cb_v.pdf",
        output_path=r"data\raw\sr_2022_cb_v_split.pdf",
        avoid_pages=[0, 16, 17],
    )
