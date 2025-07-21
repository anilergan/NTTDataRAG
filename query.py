import json
import os

import faiss
import numpy as np
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=openai_api_key)

CHUNKS_PATH = "data/chunks.jsonl"
INDEX_PATH = "db/index.faiss"

# Load chunks once
chunks = []
with open(CHUNKS_PATH, "r", encoding="utf-8") as f:
    for line in f:
        chunks.append(json.loads(line))

# Load FAISS index once
index = faiss.read_index(INDEX_PATH)

# Start interactive loop
while True:
    question = input("❓ Question: ")
    if not question.strip():
        print("👋 Exiting. Goodbye!")
        break

    # 🔹 Create embedding
    embedding_response = client.embeddings.create(
        model="text-embedding-3-small",  # or "text-embedding-3-large"
        input=question,
    )
    query_embedding = np.array(
        embedding_response.data[0].embedding, dtype="float32"
    ).reshape(1, -1)

    # 🔹 Search FAISS
    distances, indices = index.search(query_embedding, k=5)

    retrieved_chunks = [chunks[i] for i in indices[0]]
    context = "\n\n".join(
        f"[{c['main_title_of_page']} > {c['main_subtitle_of_page']} > {c['header']}] (Page {c['page']})\n{c['content']}"
        for c in retrieved_chunks
    )

    # 🔹 Ask GPT
    messages = [
        {
            "role": "system",
            "content": "You are a helpful assistant answering questions based on company reports.",
        },
        {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"},
    ]
    response = client.chat.completions.create(
        model="gpt-4o-mini",  # or gpt-4o-mini
        messages=messages,
        temperature=0.3,
    )

    # 🔹 Print answer
    print("\n🧠 Answer:")
    print(response.choices[0].message.content)

    # 🔹 Print sources
    print("\n📚 Sources:")
    for i, chunk_idx in enumerate(indices[0]):
        chunk = chunks[chunk_idx]
        similarity = 1 - distances[0][i]
        print(
            f"📄 {chunk['source']} | Page {chunk['page']} | {chunk['main_title_of_page']} > {chunk['main_subtitle_of_page']} > {chunk['header']} — 📈 Similarity: {similarity:.2f}"
        )

    print("\n👉 Do you have another question? (Press Enter to exit)")
