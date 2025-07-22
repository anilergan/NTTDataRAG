# logger.py

import logging
import os

# Logs klasörü yoksa oluştur
os.makedirs("logs", exist_ok=True)

# Logger nesnesi oluştur
logger = logging.getLogger("pdf_chunk_logger")
logger.setLevel(logging.DEBUG)

# Format
formatter = logging.Formatter(
    "[%(asctime)s] [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
)

# Console Handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)

# File Handler
file_handler = logging.FileHandler("logs/pdf_chunk.log", encoding="utf-8")
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)

# Logger’a handler’ları ekle
logger.addHandler(console_handler)
logger.addHandler(file_handler)
