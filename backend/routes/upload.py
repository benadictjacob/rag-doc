from fastapi import APIRouter, UploadFile, File, HTTPException
from backend.services.parser import extract_text
from backend.services.chunker import chunk_text
from backend.services.embeddings import generate_embedding
from backend.services.pinecone_store import upsert_vectors
from backend.services.storage import SupabaseStorage
import uuid

router = APIRouter()
supabase = SupabaseStorage()

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        # 1. Read file
        content = await file.read()
        
        # 1.5 Upload to Supabase Storage
        file_url = supabase.upload_file(content, file.filename, file.content_type)
        if not file_url:
            print(f"Warning: Supabase upload failed for {file.filename}")
            # We continue even if storage fails, just without preview URL
        
        # 2. Extract Text
        text = extract_text(content, file.filename)
        if not text:
             raise HTTPException(status_code=400, detail="Could not extract text from file or file is empty")
             
        # 3. Chunk Text
        chunks = chunk_text(text)
        
        # 4. Generate Embeddings & Prepare Vectors
        vectors = []
        for i, chunk in enumerate(chunks):
            vector_values = generate_embedding(chunk)
            if len(vector_values) == 0:
                continue
                
            vector_id = f"{file.filename}_{i}_{uuid.uuid4().hex[:6]}"
            vectors.append({
                "id": vector_id,
                "values": vector_values,
                "metadata": {
                    "document_name": file.filename,
                    "chunk_text": chunk,
                    "chunk_index": i,
                    "file_url": file_url or "" # Store URL in metadata
                }
            })
            
        # 5. Store in Pinecone
        if vectors:
            upsert_vectors(vectors)
            
        return {
            "message": "File processed successfully", 
            "chunks_count": len(vectors),
            "document_text": text,
            "file_url": file_url
        }
        
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
