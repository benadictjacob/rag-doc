from typing import Optional
import json
from backend.services.embeddings import generate_embedding
from backend.services.pinecone_store import query_vectors
from backend.services.providers import LLMEngine

llm = LLMEngine()

# Simple in-memory cache
# Maps "question|context" -> result
QUERY_CACHE = {}

def analyze_query_intent(question: str, current_document: Optional[str] = None) -> dict:
    """
    Analyzes the user's question and generates multiple search variations (Multi-Query Expansion).
    """
    json_structure = '{"is_generic": true/false, "is_current_file": true/false, "queries": ["string1", "string2", "string3"]}'
    prompt = (
        f"Analyze the user's question: '{question}'\n"
        f"Active document: {current_document or 'None'}\n\n"
        "1. Is this 'GENERIC' (chatting/greetings)?\n"
        "2. Is the user referring to 'this file' or 'current document'?\n"
        "3. If NOT generic, generate 3 different search variations of the question to improve retrieval coverage. "
        "Keep them short and focused on key entities.\n\n"
        f"Respond ONLY with a JSON object: {json_structure}."
    )
    
    try:
        response = llm.generate(prompt)
        start = response.find('{')
        end = response.rfind('}') + 1
        if start != -1 and end != -1:
            return json.loads(response[start:end])
    except Exception as e:
        print(f"[DEBUG] Multi-Query Analysis failed: {e}")
    
    return {"is_generic": False, "is_current_file": False, "queries": [question]}

def process_query(question: str, current_document: Optional[str] = None) -> dict:
    
    # 0. Check Cache (using question only for simplicity)
    cache_key = f"{question.strip().lower()}|{current_document or 'global'}"
    if cache_key in QUERY_CACHE:
        return QUERY_CACHE[cache_key]

    # 1. Analyze Intent
    intent = analyze_query_intent(question, current_document)
    if intent.get("is_generic", False):
        answer = llm.generate(f"Answer helpfully: '{question}'")
        return { "answer": answer, "sources": [] }

    # 2. Multi-Query Search
    is_current_file = intent.get("is_current_file", False)
    queries = intent.get("queries", [question])
    print(f"[DEBUG] Expanded Queries: {queries}")

    all_matches = []
    seen_ids = set()
    
    pinecone_filter = None
    if is_current_file and current_document:
        pinecone_filter = {"document_name": {"$eq": current_document}}

    for q in queries:
        vector = generate_embedding(q)
        if not vector: continue
        
        try:
            results = query_vectors(vector, top_k=5, filter=pinecone_filter)
            for match in results.get('matches', []):
                if match['id'] not in seen_ids:
                    all_matches.append(match)
                    seen_ids.add(match['id'])
        except Exception as e:
            print(f"Search error for '{q}': {e}")

    # 3. Sort by score and filter
    all_matches = sorted(all_matches, key=lambda x: x['score'], reverse=True)
    
    # Adaptive threshold: be more lenient if we have few results or it's document specific
    SIMILARITY_THRESHOLD = 0.25 if is_current_file else 0.30
    
    context_chunks = []
    sources = set()
    
    for match in all_matches[:10]: # Take top 10 unique chunks
        if match['score'] > SIMILARITY_THRESHOLD:
            text = match['metadata'].get('chunk_text', match['metadata'].get('text', ''))
            doc_name = match['metadata'].get('document_name', 'Unknown')
            context_chunks.append(text)
            sources.add(doc_name)

    # 4. Final Response
    if not context_chunks:
        answer = llm.generate(f"Explain that no document info was found for '{question}'.")
        return { "answer": answer, "sources": [] }

    context_text = "\n\n".join(context_chunks)
    prompt = (
        f"Context provided:\n{context_text}\n\n"
        f"User Question: {question}\n\n"
        "Answer strictly based on the context. If not present, state clearly."
    )
    
    try:
        answer = llm.generate(prompt)
        result = { "answer": answer, "sources": list(sources) }
        QUERY_CACHE[cache_key] = result
        return result
    except Exception as e:
        return { "answer": f"Error: {str(e)}", "sources": list(sources) }
