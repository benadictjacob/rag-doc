from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    OPENAI_API_KEY: str | None = None
    PINECONE_API_KEY: str
    PINECONE_INDEX: str
    HF_API_KEY: str
    SUPABASE_URL: str
    SUPABASE_KEY: str
    SUPABASE_BUCKET: str = "documents"

    class Config:
        env_file = ".env"

settings = Settings()
