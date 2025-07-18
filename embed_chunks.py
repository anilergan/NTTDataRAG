import os
import jsonlines
import faiss
import numpy as np
from tqdm import tqdm
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

def embed(texts):
    """
    Returns a list of embedding vectors using OpenAI embedding API.
    """
    response = client.embeddings.create(
        input=texts,
        model="text-embedding-3-small"  # or "text-embedding-ada-002"
    )
    return [np.array(d.embedding, dtype=np.float32) for d in response.data]

def main():
    input_file = "data/chunks.jsonl"
    db_folder = "db"
    os.makedirs(db_folder, exist_ok=True)

    texts = []
    metadatas = []

    with jsonlines.open(input_file, "r") as reader:
        for obj in reader:
            texts.append(obj["content"])
            metadatas.append({
                "source": obj["source"],
                "page": obj["page"]
            })

    vectors = []
    batch_size = 50

    for i in tqdm(range(0, len(texts), batch_size)):
        batch = texts[i:i+batch_size]
        vectors.extend(embed(batch))

    index = faiss.IndexFlatL2(len(vectors[0]))
    index.add(np.array(vectors))

    faiss.write_index(index, os.path.join(db_folder, "index.faiss"))

    with jsonlines.open(os.path.join(db_folder, "metadata.json"), "w") as writer:
        writer.write_all(metadatas)

    print(f"✅ Done. {len(vectors)} embeddings saved to db/")

if __name__ == "__main__":
    main()
