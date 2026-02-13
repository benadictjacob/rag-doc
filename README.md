# Production RAG System

## Project Overview
This is a production-ready Retrieval Augmented Generation (RAG) system capable of ingesting various document formats, chunking them, storing embeddings in Pinecone, and answering questions using OpenAI with a HuggingFace fallback.

## Architecture Explanation
- **Backend**: FastAPI
- **Database**: Pinecone (Serverless)
- **AI Models**: 
    - OpenAI GPT-3.5 Turbo (Primary Generation)
    - OpenAI text-embedding-3-small (Embeddings)
    - Mistral-7B-Instruct via HuggingFace Inference API (Fallback Generation)
- **Frontend**: Vanilla HTML/JS

## Setup Instructions
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Create `.env` file from `.env.example` and populate API keys.

## Environment Variables
- `OPENAI_API_KEY`: Your OpenAI API key
- `PINECONE_API_KEY`: Pinecone API Key
- `PINECONE_INDEX`: Name of your index (e.g., "rag-demo")
- `HF_API_KEY`: HuggingFace User Access Token

## Running Locally
```bash
uvicorn backend.main:app --reload
```
Open `http://localhost:8000` to view the application.

## Deployment Instructions
- Can be deployed to any Docker-compatible hosting (Render, Railway, AWS).
- Ensure environment variables are set in the production environment.
- Use a production WSGI server like Gunicorn with Uvicorn workers.

## Design Decisions
- **Fallback**: Implemented a robust fallback to HuggingFace to ensure high availability if OpenAI is down or rate-limited.
- **Modular Services**: Separated concerns (Parser vs Chunker vs Embeddings) for easy testing and replacement.
- **Direct Decoding**: For unknown files, attempted UTF-8 decoding to be permissive.

## Limitations
- In-memory processing of file uploads (large files might consume RAM).
- Basic chunking strategy without overlapping sentence awareness.

## Future Improvements
- Add semantic chunking.
- Add user authentication.
- Add history/memory to chat.
