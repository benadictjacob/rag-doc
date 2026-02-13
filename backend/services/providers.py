from abc import ABC, abstractmethod
from huggingface_hub import InferenceClient
from backend.config import settings

class ModelProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str) -> str:
        pass

class HFProvider(ModelProvider):
    def __init__(self):
        self.client = InferenceClient(token=settings.HF_API_KEY)

    def generate(self, prompt: str) -> str:
        # Using Mistral-7B-Instruct via HuggingFace Inference API (free)
        messages = [{"role": "user", "content": prompt}]
        response = self.client.chat_completion(
            messages, 
            max_tokens=500, 
            model="mistralai/Mistral-7B-Instruct-v0.2"
        )
        return response.choices[0].message.content

class OpenAIProvider(ModelProvider):
    def __init__(self):
        if not settings.OPENAI_API_KEY:
            self.available = False
            return
            
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
            self.available = True
        except Exception:
            self.available = False

    def generate(self, prompt: str) -> str:
        if not self.available:
            raise Exception("OpenAI not available")
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500
        )
        return response.choices[0].message.content

class LLMEngine:
    def __init__(self):
        # HuggingFace is now primary (free), OpenAI is fallback
        self.primary = HFProvider()
        self.fallback = OpenAIProvider()

    def generate(self, prompt: str) -> str:
        try:
            return self.primary.generate(prompt)
        except Exception as e:
            print(f"Primary (HF) failed: {e}. Trying OpenAI fallback.")
            try:
                return self.fallback.generate(prompt)
            except Exception as e2:
                return f"Error: Both providers failed. HF: {e}, OpenAI: {e2}"
