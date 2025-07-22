# merge_chunks.py
import json
from pathlib import Path

INPUT_FILES = [
    "data/chunks/chunks_pdf_2020.jsonl",
    "data/chunks/chunks_pdf_2022.jsonl",
    "data/chunks/chunks_pdf_2023.jsonl",
    "data/chunks/chunks_pdf_2024.jsonl",
]

OUTPUT_FILE = "data/merged_chunks.jsonl"

with open(OUTPUT_FILE, "w", encoding="utf-8") as outfile:
    for file_path in INPUT_FILES:
        with open(file_path, "r", encoding="utf-8") as infile:
            for line in infile:
                line = line.strip()
                if not line:
                    continue  # boş satırı atla
                json_obj = json.loads(line)
                json.dump(json_obj, outfile)
                outfile.write("\n")

print(f"✅ Merged {len(INPUT_FILES)} files into {OUTPUT_FILE}")
