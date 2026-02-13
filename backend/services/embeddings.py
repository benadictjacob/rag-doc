import requests
from backend.config import settings
import time

# New HF Router Endpoint
API_URL = "https://router.huggingface.co/hf-inference/models/sentence-transformers/all-MiniLM-L6-v2/pipeline/feature-extraction"
HEADERS = {"Authorization": f"Bearer {settings.HF_API_KEY}"}

def generate_embedding(text: str, retries=3) -> list[float]:
    for attempt in range(retries):
        try:
            response = requests.post(API_URL, headers=HEADERS, json={"inputs": text}, timeout=10)
            
            if response.status_code != 200:
                print(f"[ERROR] Embedding API Error ({response.status_code}): {response.text}")
                # Wait before retry if server error
                if response.status_code >= 500:
                    time.sleep(1)
                    continue
                return []

            result = response.json()
            
            # Handle different return formats from HF
            # Expected: [0.1, 0.2, ...] or [[0.1, 0.2, ...]]
            if isinstance(result, list):
                if len(result) > 0 and isinstance(result[0], list):
                    return result[0] # Return first embedding if batch
                return result # Return direct list
            
            print(f"[ERROR] Unexpected embedding format: {type(result)}")
            return []

        except Exception as e:
            print(f"[ERROR] Embedding Generation Failed (Attempt {attempt+1}/{retries}): {e}")
            time.sleep(1)
            
    return []
