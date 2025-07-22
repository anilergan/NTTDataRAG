# 🧠 NTTDataRAG

**NTTDataRAG** is an end-to-end Retrieval-Augmented Generation (RAG) pipeline tailored to extract, process, index, and retrieve answers from complex annual PDF reports using OpenAI's embedding and language models.

---

## 🗂 Project Structure

```
NTTDATARAG/
├── .pytest_cache/                  # pytest's internal cache (ignored)
├── case/                           # Case study presentation and materials
├── img/                            # Images (diagrams, architecture, README assets)
│
├── src/                            # Main application source code
│   ├── __pycache__/                # Python bytecode cache (ignored)
│   ├── data/                       # Persistent data (chunks, embeddings, FAISS index)
│   │   └── ...                     # e.g., chunks/, embeddings.jsonl, faiss_index.faiss
│   ├── logs/                       # Runtime logs and QA logs
│   ├── section_boxes/             # Bounding box visualization tools
│   │   ├── draw_page_section_boxes.py  # Draws labeled sections on PDF pages
│   │   └── utils.py                    # Helper functions for visual debugging
│   ├── app.py                      # (Optional) FastAPI app for serving endpoints
│   ├── config.py                   # Page ranges and coordinates for chunk extraction
│   ├── embedding.py                # Embedding logic using OpenAI API
│   ├── logger.py                   # Custom logging setup
│   ├── merge_chunks.py             # Merges multiple chunk `.jsonl` files
│   ├── pdf_2020_chunker_by_span_analysis.py  # Year-specific chunker (2020 format)
│   ├── pdf_2024_chunker_by_span_analysis.py  # Year-specific chunker (2024 format)
│   ├── pdf_chunker_by_template.py       # Template-based PDF chunking logic
│   ├── pdf_span_analyser.py             # Font, size, color and bbox analysis on spans
│   ├── query.py                   # CLI-based interactive Q&A interface
│   ├── rag_pipeline.py            # Full pipeline: chunk → embed → index → QA
│   ├── retriever.py               # FAISS indexing and similarity retrieval
│   └── split_double_pages_pdfs.py       # Splits 2-in-1 scanned PDF pages in half
│
├── tests/                          # Pytest unit tests
│   ├── __pycache__/                # Bytecode cache for tests (ignored)
│   ├── test_chunker.py             # Tests for chunking logic
│   ├── test_embedding.py           # Tests for embedding output and shape
│   ├── test_output.log             # Saved output from latest test run (optional)
│   └── test_retriever.py           # Tests for FAISS indexing and retrieval
│
├── .gitignore                      # Git ignore rules
├── .dockerignore                   # Ignore rules for Docker builds
├── Dockerfile                      # Docker image setup and build instructions
├── .env                            # Environment variables (e.g., OpenAI API key)
├── pyproject.toml                  # Poetry project config (dependencies, pytest options)
├── poetry.lock                     # Locked dependency versions for reproducibility
├── README.md                       # Project overview, instructions, diagrams
├── QATEST.md                       # QA checklist and test cases
└── TODO.md                         # Technical tasks and future improvements

```

---

## 🚀 Features

- 📄 **Custom PDF Chunking**: Layout-aware chunking tailored for multi-column business reports
- 🧠 **OpenAI Embeddings**: `text-embedding-3-small` support
- 🔍 **Semantic Search**: FAISS-based vector similarity retrieval
- 💬 **Natural Language QA**: GPT-4o model (gpt-4o-mini) answering contextually
- 🌐 **API Access**: Query the system via REST with FastAPI
- 🐳 **Dockerized**: Fully containerized for portable deployment

---

## ⚙️ Installation

> Python 3.11+, Poetry is required.

```bash
# Clone and install
git clone https://github.com/anilergan/NTTDataRAG.git
cd nttdatarag

# Install dependencies via Poetry
poetry install

# Create a `.env` file with your OpenAI key
echo "OPENAI_API_KEY=sk-..." > .env
```
---
## 🧱 Manual Chunking Strategy (Before Pipeline)

Before automating the entire pipeline, we implemented manual chunking logic tailored for each PDF structure. Since the layout of NTT Data's PDF reports can vary drastically from year to year, we used **two different chunking strategies** depending on the structural consistency of the document.

---

### 📌 1. Template-Based Chunking

Used for:  
- `sr_2022_cb_v_split.pdf`  
- `sr_2023_cb_v.pdf`  

These PDFs have a **highly regular and repeatable layout**, with each section (e.g., *Social Issues*, *Business Need*, *Solution*, *Impact*) occupying a **fixed and clearly defined area** on the page. Because of this:

- We manually defined section boxes using coordinates in pixels → converted to points.
- These coordinates are stored in `config.py` as `SECTION_COORDINATES_DICT_PDF_2022` and `SECTION_COORDINATES_DICT_PDF_2023`.
- The script `draw_page_section_boxes.py` helps visualize and verify these boxes.
- The chunking logic uses these regions to extract structured data directly.

---

### 📌 2. Span-Based Chunking (Using Text Styling & Layout)

Used for:  
- `sr_2020_cb_p.pdf`  
- `sr_2024_cb_v.pdf`  

These PDFs **lack a rigid structural layout**, but show strong patterns in **text spans** such as font size, font family, position (`BBox`), and color. Therefore:

- We used `pdf_span_analyser.py` to inspect and analyze span-level details for each page.
- Based on patterns (e.g., heading fonts, color = 0, bold sizes), we defined rules to extract `main_title_of_page`, `main_subtitle_of_page`, and each section.
- For 2024: Sections had consistent relative positions (e.g., "Business Need" always below "Social Issues", etc.).
- For 2020: We mainly relied on span color and typography to identify key sections and transitions.

---

### 📊 Supporting Tools

#### ✅ `pdf_span_analyser.py`
Helps inspect spans in a given page and extract metadata like font, color, size, and position.

#### ✅ `draw_page_section_boxes.py`
Used only in template-based PDFs to visually verify the chunk boundaries. Output images are saved as `.jpg` in the `section_boxes/` folder.

Example output:
```
section_boxes/sr_2023_cb_v_page17_sections.jpg
```

---

These manual chunking tools allowed us to build a reliable foundation for downstream embedding, indexing, and retrieval. They are crucial for adapting the pipeline to multiple document formats and layouts.


---

## 📌 Usage

### 1️⃣ Run Full Pipeline (Chunk → Embed → Index → QA Loop)

```bash
poetry run python rag_pipeline.py
```

This will:
- Chunk the PDF (based on `config.py`)
- Generate embeddings and save
- Build FAISS index
- Start interactive CLI Q&A

### 2️⃣ Query via API

```bash
poetry run uvicorn app:app --reload
```

- Go to [http://localhost:8000/docs](http://localhost:8000/docs) for Swagger UI
- Example POST:

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is TradeWaltz and how much efficiency did it provide?"}'
```

### 3️⃣ Build Docker Image

```bash
docker build -t ntt-rag .
```

### 4️⃣ Run in Container

```bash
docker run --env-file .env -p 8000:8000 ntt-rag
```

---

## 🧪 Testing

```
├── test_chunker.py             # Tests for chunking logic
├── test_embedding.py           # Tests for embedding output and shape
├── test_output.log             # Saved output from latest test run (optional)
└── test_retriever.py           # Tests for FAISS indexing and retrieval
```

```bash
poetry add --dev pytest
poetry run pytest tests/
# In order to get log outputs for tests:
poetry run pytest tests/ -v | tee tests/test_output.log
```

## 📐 Architecture Diagram

![Architecture Diagram](img/architecutral_diagram.png)


## 📚 Sources

This project was developed for a case study on document understanding and retrieval using OpenAI technologies and complex business PDFs from NTT Data.

---

## 🧑‍💻 Author

**Anıl Ergan** – `ergananil@gmail.com`

---

## ✅ License

This repository is licensed for demonstration, academic, and internal review purposes.
