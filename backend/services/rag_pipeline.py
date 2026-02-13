from typing import Optional
import json
from backend.services.embeddings import generate_embedding
from backend.services.pinecone_store import query_vectors
from backend.services.providers import LLMEngine

llm = LLMEngine()

# Simple in-memory cache
# Maps "question|context" -> result
QUERY_CACHE = {}

def determine_search_scope(question: str, current_context: Optional[str]) -> dict:
    """
    Uses LLM to decide on search scope filters.
    Returns a Pinecone filter dict or None.
    """
    if not current_context:
        # If no context is active, default to global search unless specified otherwise
        # But we could still check if user asks for specific file
        pass

    # Router Prompt
    json_structure = '{"scope": "ALL" | "CURRENT" | "SPECIFIC", "target_file": "string or null"}'
    prompt = (
        f"You are a query router. Analyze the user's question.\n"
        f"Current open document: {current_context or 'None'}\n"
        f"Question: {question}\n\n"
        "Determine the search scope:\n"
        "- CURRENT: If the question implies the open document (e.g., 'summarize this', 'what does it say').\n"
        "- ALL: If the question is general or asks about multiple files (e.g., 'find in all files', 'compare', or no specific target).\n"
        "- SPECIFIC: If the question queries a specific different file (e.g., 'check the resume', 'in invoice.pdf').\n\n"
        f"Respond ONLY with a JSON object: {json_structure}."
    )
    
    try:
        response = llm.generate(prompt)
        # Clean response to ensure JSON
        start = response.find('{')
        end = response.rfind('}') + 1
        if start != -1 and end != -1:
            data = json.loads(response[start:end])
            
            scope = data.get('scope', 'ALL')
            
            if scope == 'CURRENT' and current_context:
                print(f"[DEBUG] Router: Scoping to CURRENT ({current_context})")
                return {"document_name": {"$eq": current_context}}
                
            if scope == 'SPECIFIC' and data.get('target_file'):
                # Start of fuzzy matching logic (omitted for now, assuming user speaks clearly or we match loosely)
                # For this demo, we'll try to use the target as a strict filter if it looks like a filename
                # Or simplistic: just return metadata filter
                target = data['target_file']
                print(f"[DEBUG] Router: Scoping to SPECIFIC ({target})")
                return {"document_name": {"$eq": target}} # Pinecone syntax
                
            print(f"[DEBUG] Router: Scoping to ALL")
            return None
            
    except Exception as e:
        print(f"[DEBUG] Router failed: {e}. Defaulting to ALL/Global.")
        return None
        
    return None

def process_query(question: str, current_document: Optional[str] = None) -> dict:
    
    # 0. Check Cache
    cache_key = f"{question.strip().lower()}|{current_document or 'global'}"
    if cache_key in QUERY_CACHE:
        print(f"[DEBUG] Cache Hit for: {cache_key}")
        return QUERY_CACHE[cache_key]

    # 1. Determine Scope (Filter)
    # Only run router if we have a current_document or query looks specific
    # To save latency, we can use heuristics:
    # If strictly generic ("Hi"), skip.
    pinecone_filter = determine_search_scope(question, current_document)

    # 2. Embed question
    vector = generate_embedding(question)
    
    if len(vector) == 0:
        return {
            "answer": "Error: Could not generate embedding. Please try again.",
            "sources": []
        }
    
    # 3. Retrieve chunks with Filter
    try:
        # Increase top_k slightly for scoped search
        results = query_vectors(vector, top_k=8, filter=pinecone_filter)
    except Exception as e:
        print(f"Pinecone query error: {e}")
        return {
            "answer": f"Error querying database: {str(e)}",
            "sources": []
        }
    
    # 4. Assess Relevance & Routing
    matches = results.get('matches', [])
    context_chunks = []
    sources = set()
    
    # Similarity Threshold for "Relevance"
    # If top match is below this, we assume the doc doesn't have the answer
    # and treat it as a generic question.
    SIMILARITY_THRESHOLD = 0.35 
    
    best_score = matches[0]['score'] if matches else 0
    print(f"[DEBUG] Best Similarity Score: {best_score}")

    for match in matches:
        score = match.get('score', 0)
        if score > SIMILARITY_THRESHOLD:
            text = match['metadata'].get('chunk_text', match['metadata'].get('text', ''))
            doc_name = match['metadata'].get('document_name', 'Unknown')
            context_chunks.append(text)
            sources.add(doc_name)
    
    # 5. Routing Logic (Conversational vs RAG)
    
    # CASE A: Low Similarity / No Context -> Generic/Conversational
    if not context_chunks:
        print(f"[DEBUG] Low similarity ({best_score} < {SIMILARITY_THRESHOLD}). Switching to Generic/Conversational.")
        
        # If user explicitly asked about the current doc but we found nothing
        if current_document:
             fallback_prompt = (
                f"You are Aggroso. User asked: '{question}'.\n"
                f"Context: The user is looking at '{current_document}', but I couldn't find any relevant info in it (similarity score {best_score:.2f}).\n"
                "Answer the user's question using your general knowledge, but mention that the document doesn't seem to contain this information."
            )
        else:
            # Purely generic chat
            fallback_prompt = (
                f"You are Aggroso, an intelligent assistant. User asked: '{question}'.\n"
                "Answer the question helpfully using your general knowledge."
            )

        try:
            answer = llm.generate(fallback_prompt)
        except Exception as e:
            answer = f"Error: {str(e)}"
            
        result = { "answer": answer, "sources": [] }
        QUERY_CACHE[cache_key] = result
        return result

    # CASE B: RAG Mode (High Similarity)
    print(f"[DEBUG] RAG Mode. Sources: {len(sources)}")
    context_text = "\n\n".join(context_chunks)
    
    system_instruction = (
        "You are an intelligent assistant analyzing the provided document context. "
        "Strictly answer the question using ONLY the provided context. "
        "If the context contains the answer, verify it matches the user's question. "
        "If the context is irrelevant to the specific question, ignore it and say you couldn't find the answer in the document."
    )
    prompt = f"{system_instruction}\n\nContext:\n{context_text}\n\nQuestion: {question}\n\nAnswer:"
    
    try:
        answer = llm.generate(prompt)
    except Exception as e:
        return { "answer": f"Error: {str(e)}", "sources": list(sources) }
    
    result = { "answer": answer, "sources": list(sources) }
    QUERY_CACHE[cache_key] = result
    return result
