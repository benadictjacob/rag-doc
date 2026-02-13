from fastapi import APIRouter
from backend.config import settings
from backend.services.pinecone_store import pc
from openai import OpenAI
import requests

router = APIRouter()

@router.get("/health")
def health_check():
    status = {
        "backend": "running",
        "pinecone": "unknown",
        "openai": "unknown",
        "huggingface": "unknown"
    }
    
    # Check Pinecone
    try:
        pc.list_indexes()
        status["pinecone"] = "reachable"
    except Exception as e:
        status["pinecone"] = f"unreachable: {str(e)}"

    # Check OpenAI
    try:
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        client.models.list()
        status["openai"] = "reachable"
    except Exception as e:
        status["openai"] = f"unreachable: {str(e)}"
        
    # Check HuggingFace
    try:
        res = requests.get("https://huggingface.co/api/models", timeout=5)
        if res.status_code == 200:
            status["huggingface"] = "reachable"
        else:
             status["huggingface"] = f"unreachable: {res.status_code}"
    except Exception as e:
        status["huggingface"] = f"unreachable: {str(e)}"

    # Check Supabase
    try:
        from backend.services.storage import SupabaseStorage
        store = SupabaseStorage()
        if store.client:
            buckets = store.client.storage.list_buckets()
            status["supabase"] = {
                "status": "reachable",
                "buckets": [b.name for b in buckets],
                "configured_bucket": store.bucket
            }
        else:
            status["supabase"] = "client_init_failed"
    except Exception as e:
        status["supabase"] = f"unreachable: {str(e)}"
        
    return status
