from pinecone import Pinecone, ServerlessSpec
from backend.config import settings
import time

pc = Pinecone(api_key=settings.PINECONE_API_KEY)

INDEX_NAME = settings.PINECONE_INDEX

def get_index():
    if INDEX_NAME not in [index.name for index in pc.list_indexes()]:
        pc.create_index(
            name=INDEX_NAME,
            dimension=384, # sentence-transformers/all-MiniLM-L6-v2 dimension
            metric="cosine",
            spec=ServerlessSpec(
                cloud="aws",
                region="us-east-1"
            )
        )
        while not pc.describe_index(INDEX_NAME).status['ready']:
            time.sleep(1)
            
    return pc.Index(INDEX_NAME)

def upsert_vectors(vectors):
    index = get_index()
    # Batch upsert is recommended but simple upsert for demo
    index.upsert(vectors=vectors)

def query_vectors(vector, top_k=5, filter=None):
    index = get_index()
    return index.query(vector=vector, top_k=top_k, include_metadata=True, filter=filter)

def delete_all_vectors():
    index = get_index()
    try:
        index.delete(delete_all=True)
        print(f"[INFO] All vectors deleted from index '{INDEX_NAME}'")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to delete vectors: {e}")
        return False
