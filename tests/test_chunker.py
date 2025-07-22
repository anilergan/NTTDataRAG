import pytest
from pdf_chunker_by_template import extract_chunks_by_template
from config import SECTION_COORDINATES_DICT_PDF_2023
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

def test_extract_chunks_structure():
    pdf_path = "data/raw/sr_2023_cb_v.pdf"
    pages = [17]
    coords = SECTION_COORDINATES_DICT_PDF_2023
    chunks = extract_chunks_by_template(pdf_path, pages, coords)
    assert isinstance(chunks, list)
    for chunk in chunks:
        assert "header" in chunk
        assert "content" in chunk
        assert "page" in chunk
