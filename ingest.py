import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI
import chromadb

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

client = OpenAI()

# -----------------------------
# CHROMA DATABASE
# -----------------------------

chroma_client = chromadb.PersistentClient(path=str(BASE_DIR / "chroma_db"))

collection = chroma_client.get_or_create_collection(
    name="persona"
)

# Optional: clear old database
# collection.delete(where={})

docs = []

docs_dir = BASE_DIR / "documents"

for filename in os.listdir(docs_dir):

    if not filename.endswith(".txt"):
        continue

    with open(docs_dir / filename, "r", encoding="utf-8") as f:

        text = f.read()

        docs.append({
            "filename": filename,
            "text": text
        })

chunks = []

chunk_size = 1200
overlap = 200

for doc in docs:

    text = doc["text"]
    filename = doc["filename"]

    for i in range(0, len(text), chunk_size - overlap):

        chunk = text[i:i + chunk_size]

        chunks.append({
            "text": chunk,
            "source": filename
        })

print("Creating embeddings...")

for i, chunk_data in enumerate(chunks):

    chunk_text = chunk_data["text"]

    embedding = client.embeddings.create(
        model="text-embedding-3-small",
        input=chunk_text
    ).data[0].embedding

    collection.add(
        ids=[str(i)],
        documents=[chunk_text],
        embeddings=[embedding],
        metadatas=[{
            "source": chunk_data["source"]
        }]
    )

    print(f"Added chunk {i}")

print("Embeddings stored.")