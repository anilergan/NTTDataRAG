import json
import os
import random
from datetime import datetime
import faiss
import numpy as np
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=openai_api_key)

CHUNKS_PATH = r"data\merged_chunks.jsonl"
INDEX_PATH = r"data\faiss_index.faiss"
LOG_PATH = "logs/QA.log"
os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)


def log_qa(question: str, answer: str):
    """Logs Q&A to a classic timestamped .log file format."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] [INFO] Q: {question}\n")
        f.write(f"[{timestamp}] [INFO] A: {answer.strip()}\n\n")


def load_chunks(path: str):
    """Load JSONL chunks from disk once."""
    chunks = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            chunks.append(json.loads(line))
    return chunks


def load_index(path: str):
    """Load FAISS index from disk once."""
    return faiss.read_index(path)


def interactive_qa_loop(chunks, index):
    """Ana interaktif soru-cevap döngüsü."""
    while True:
        question = input("❓ Question: ")
        if not question.strip():
            print("👋 Exiting. Goodbye!")
            break

        # Create embedding
        resp = client.embeddings.create(
            model="text-embedding-3-small",
            input=question,
        )
        qvec = np.array(resp.data[0].embedding, dtype="float32").reshape(1, -1)

        # Search FAISS
        distances, indices = index.search(qvec, k=5)
        max_sim = distances[0][0]

        # Fallback düşük benzerlik için
        if max_sim < 0.5:
            user_lang = "tr" if any(ch in question for ch in "ığüşöç") else "en"
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
            print("\n🧠 Answer:")
            print(random.choice(fallback[user_lang]))
            print(f"\n📚 Sources: No reliable sources found (max similarity {max_sim:.2f})\n")
            continue

        # Build context
        retrieved = [chunks[i] for i in indices[0]]
        context = "\n\n".join(
            f"[{c['main_title_of_page']} > {c['main_subtitle_of_page']} > {c['header']}] (Page {c['page']})\n{c['content']}"
            for c in retrieved
        )

        # Ask GPT
        messages = [
            {"role": "system", "content": "You are a helpful assistant answering questions based on company reports."},
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"},
        ]
        chat = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.3,
        )
        answer = chat.choices[0].message.content

        # Log & print
        log_qa(question, answer)
        print("\n🧠 Answer:")
        print(answer)
        print("\n📚 Sources:")
        for sim, idx in zip(distances[0], indices[0]):
            c = chunks[idx]
            print(f"📄 {c['source']} | Page {c['page']} | {c['header']} — 📈 Similarity: {sim:.2f}")
        print("\n👉 Do you have another question? (Press Enter to exit)")


def main():
    chunks = load_chunks(CHUNKS_PATH)
    index = load_index(INDEX_PATH)
    interactive_qa_loop(chunks, index)


if __name__ == "__main__":
    main()
