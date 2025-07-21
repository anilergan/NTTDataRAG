PAGES_TO_USE_PDF_2020 = [page for page in range(3, 14)] + [
    page for page in range(15, 18)
]

PAGES_TO_USE_PDF_2022 = (
    [page for page in range(5, 13)]
    + [page for page in range(14, 21)]
    + [22]
    + [page for page in range(23, 33)]
)


PAGES_TO_USE_PDF_2023 = (
    [page for page in range(6, 16)]
    + [page for page in range(17, 28)]
    + [page for page in range(29, 36)]
)


PAGES_TO_USE_PDF_2024 = (
    [page for page in range(7, 24)]
    + [page for page in range(25, 35)]
    + [36, 37]
    + [page for page in range(39, 42)]
    + [44, 46, 47, 47, 49]
)

SECTION_COORDINATES_DICT_PDF_2022 = {
    "main_title_of_page": ((60, 260), (1200, 460)),
    "main_subtitle_of_page": ((60, 462), (1200, 562)),
    "substance_1": ((60, 1020), (610, 1670)),
    "substance_2": ((620, 1020), (1200, 1670)),
    "key_metrics": ((60, 565), (1200, 1020)),
}

SECTION_COORDINATES_DICT_PDF_2023 = {
    "main_title_of_page": ((40, 115), (338, 270)),
    "main_subtitle_of_page": ((350, 115), (1500, 270)),
    "social_issues": ((250, 270), (1500, 420)),
    "substance_1": ((40, 425), (595, 1180)),
    "substance_2": ((605, 425), (1220, 1180)),
    "key_metrics": ((1225, 425), (1740, 1180)),
}
