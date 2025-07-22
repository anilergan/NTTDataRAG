# app.py
# poetry run uvicorn app:app --reload

import os
import json
import random
from typing import List
from fastapi import FastAPI, Request
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import OpenAI
import numpy as np
import faiss

# === Yüklemeler ve ayarlar ===
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=openai_api_key)

CHUNKS_PATH = "src/data/merged_chunks.jsonl"
INDEX_PATH = "src/data/faiss_index.faiss"

# === FastAPI nesnesi ===
app = FastAPI(title="NTT RAG Pipeline API")

# === Chunk ve Index yükle ===
with open(CHUNKS_PATH, "r", encoding="utf-8") as f:
    chunks = [json.loads(line) for line in f]

index = faiss.read_index(INDEX_PATH)

# === Request-Response modelleri ===
class AskRequest(BaseModel):
    question: str

class AskResponse(BaseModel):
    answer: str
    sources: List[str]

# === Sağlık kontrolü ===
@app.get("/health")
def health_check():
    return {"status": "ok"}

# === Ana soru-cevap endpoint’i ===
@app.post("/ask", response_model=AskResponse)
def ask_question(request: AskRequest):
    question = request.question.strip()

    # 🔹 Embed soruyu
    resp = client.embeddings.create(
        model="text-embedding-3-small",
        input=question,
    )
    qvec = np.array(resp.data[0].embedding, dtype="float32").reshape(1, -1)

    # 🔹 FAISS araması
    distances, indices_ = index.search(qvec, k=5)
    max_sim = distances[0][0]

    # 🔹 Düşük benzerlik fallback
    if max_sim < 0.5:
        user_lang = "tr" if any(ch in question for ch in "üğşıçö") else "en"
        fallback = {
            "en": [
                "Sorry, I couldn't find any relevant information in the available documents.",
                "I'm not confident enough to answer that based on the provided sources.",
                "This question seems to be outside the scope of the documents I'm trained on.",
            ],
            "tr": [
                "Üzgünüm, elimdeki belgelerde bu soruya dair güvenilir bir bilgi bulamadım.",
                "Bu soruya mevcut kaynaklara dayanarak sağlıklı bir yanıt veremem.",
                "Bu soru, elimdeki belgelerin kapsamının dışında görünüyor.",
            ],
        }
        return AskResponse(answer=random.choice(fallback[user_lang]), sources=[])

    # 🔹 Bağlam oluştur
    retrieved = [chunks[i] for i in indices_[0]]
    context = "\n\n".join(
        f"[{c['main_title_of_page']} > {c['main_subtitle_of_page']} > {c['header']}] (Page {c['page']})\n{c['content']}"
        for c in retrieved
    )

    # 🔹 LLM'e gönder
    messages = [
        {"role": "system", "content": "You are a helpful assistant answering questions based on company reports."},
        {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"},
    ]
    chat = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0.3,
    )
    answer = chat.choices[0].message.content.strip()

    # 🔹 Kaynakları toparla
    sources = [
        f"{c['source']} | Page {c['page']} | {c['header']} | Similarity: {distances[0][i]:.2f}"
        for i, c in enumerate(retrieved)
    ]

    return AskResponse(answer=answer, sources=sources)
