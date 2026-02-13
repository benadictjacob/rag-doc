from typing import List

def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    chunks = []
    start = 0
    text_len = len(text)

    if text_len <= chunk_size:
        return [text]

    while start < text_len:
        end = min(start + chunk_size, text_len)
        chunk = text[start:end]
        chunks.append(chunk)
        
        # Move start forward, but backtrack by overlap
        start += chunk_size - overlap
        
        # Ensure we don't get stuck in an infinite loop if overlap >= chunk_size 
        # (though default values prevent this)
        if start >= text_len:
            break
            
    return chunks
