📋 TODO.md  
NTT Data RAG Mini Project – AI Engineer Case Study

✅ 1. Data Collection  
[x] Downloaded PDF reports from 2019 to 2024  
[x] Placed all reports inside the `data/` folder  

✅ 2. PDF Chunking  
[x] Created `pdf_chunker.py`  
[x] Extracted text page-by-page from PDFs  
[x] Saved chunks into `chunks.jsonl` with metadata  

🔜 3. Embedding  
[x] Create `embed_chunks.py`  
[x] Generate embeddings for each chunk in `chunks.jsonl`  
[x] Store vectors in a FAISS (or similar) vector database under `db/`  

🔜 4. Q&A Pipeline  
[ ] Create `query.py`  
[ ] Accept user question and retrieve top relevant chunks  
[ ] Use OpenAI or another LLM to generate answers based on context  

🔜 5. Dockerization  
[ ] Write `Dockerfile`  
[ ] Ensure the entire project runs with a single command  
[ ] Add `.env`, `requirements.txt` or `pyproject.toml` if needed  

🔜 6. Final Delivery & Demo  
[ ] Clean up project structure  
[ ] Write `README.md` (project description + how to run)  
[ ] Optional: create a simple CLI or notebook demo  
