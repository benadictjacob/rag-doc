from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from backend.services.rag_pipeline import process_query

router = APIRouter()

class QueryRequest(BaseModel):
    question: str
    current_document: Optional[str] = None # Filename the user is currently looking at

@router.post("/ask")
def ask_question(request: QueryRequest):
    try:
        if not request.question:
            raise HTTPException(status_code=400, detail="Question cannot be empty")
            
        result = process_query(request.question, request.current_document)
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
