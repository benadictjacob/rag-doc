import requests
import json
import time

BASE_URL = "http://127.0.0.1:8000"

def test_health():
    print(f"\n--- Testing Health Check ---")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=15)
        print("Status Code:", response.status_code)
        print("Response:", response.text)
        return response.status_code == 200
    except Exception as e:
        print(f"Health check failed: {e}")
        return False

def test_query(question, current_doc=None):
    print(f"\n--- Testing Question: '{question}' (Doc: {current_doc}) ---")
    try:
        payload = {"question": question, "current_document": current_doc} 
        print("Sending request...")
        response = requests.post(f"{BASE_URL}/ask", json=payload, timeout=30)
        
        if response.status_code == 200:
            print("Response:", json.dumps(response.json(), indent=2))
        else:
            print(f"Error {response.status_code}: {response.text}")
            
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    print("Bypassing health check, testing queries directly...")
    # Test Generic
    test_query("Hi, how are you?")
    # Test RAG Specific (Global)
    test_query("What is the invoice number?") 
    # Test "This File" logic
    test_query("Explain about this file.", current_doc="test.pdf")
