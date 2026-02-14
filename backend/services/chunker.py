from typing import List

def chunk_text(text: str, chunk_size: int = 600, overlap: int = 100) -> List[str]:
    """
    Chunks text by looking for natural boundaries (paragraphs, then sentences).
    Ensures that context is preserved better than naive character splitting.
    """
    if not text:
        return []

    # 1. Normalize whitespace
    text = text.replace('\r\n', '\n').strip()
    
    # 2. Split into potential blocks (paragraphs)
    paragraphs = text.split('\n\n')
    
    chunks = []
    current_chunk = ""
    
    for para in paragraphs:
        # If adding this paragraph exceeds chunk size, we need to handle it
        if len(current_chunk) + len(para) > chunk_size:
            # If current_chunk is not empty, save it
            if current_chunk:
                chunks.append(current_chunk.strip())
                # Start new chunk with overlap from previous
                # Taking the last 'overlap' characters as a rough buffer
                overlap_text = current_chunk[-overlap:] if len(current_chunk) > overlap else current_chunk
                current_chunk = overlap_text + "\n" + para
            else:
                # If a single paragraph is larger than chunk_size, split it by sentence
                sentences = para.replace('! ', '. ').replace('? ', '. ').split('. ')
                for sentence in sentences:
                    if len(current_chunk) + len(sentence) > chunk_size:
                        if current_chunk:
                            chunks.append(current_chunk.strip())
                            overlap_text = current_chunk[-overlap:] if len(current_chunk) > overlap else current_chunk
                            current_chunk = overlap_text + " " + sentence
                        else:
                            # Sentence itself is huge, fallback to hard cut
                            sub_chunks = [sentence[i:i+chunk_size] for i in range(0, len(sentence), chunk_size)]
                            chunks.extend(sub_chunks[:-1])
                            current_chunk = sub_chunks[-1]
                    else:
                        current_chunk += " " + sentence if current_chunk else sentence
        else:
            current_chunk += "\n\n" + para if current_chunk else para

    if current_chunk:
        chunks.append(current_chunk.strip())
        
    return [c for c in chunks if c.strip()]
