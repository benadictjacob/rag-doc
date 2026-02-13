import io
import json
import csv
from pypdf import PdfReader

def extract_text(file_bytes: bytes, filename: str) -> str:
    original_filename = filename.lower()
    
    try:
        if original_filename.endswith('.pdf'):
            return _parse_pdf(file_bytes)
        elif original_filename.endswith('.csv'):
            return _parse_csv(file_bytes)
        elif original_filename.endswith('.json'):
            return _parse_json(file_bytes)
        elif original_filename.endswith('.txt') or original_filename.endswith('.md'):
            return file_bytes.decode('utf-8', errors='ignore')
        else:
            # Fallback for unknown types
            return file_bytes.decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"Error parsing file {filename}: {e}")
        return ""

def _parse_pdf(file_bytes: bytes) -> str:
    reader = PdfReader(io.BytesIO(file_bytes))
    text = []
    for page in reader.pages:
        extracted = page.extract_text()
        if extracted:
            text.append(extracted)
    return "\n".join(text)

def _parse_csv(file_bytes: bytes) -> str:
    content = file_bytes.decode('utf-8', errors='ignore')
    reader = csv.reader(io.StringIO(content))
    lines = []
    for row in reader:
        lines.append(" ".join(row))
    return "\n".join(lines)

def _parse_json(file_bytes: bytes) -> str:
    content = file_bytes.decode('utf-8', errors='ignore')
    data = json.loads(content)
    return _flatten_json(data)

def _flatten_json(y) -> str:
    out = []
    def flatten(x):
        if type(x) is dict:
            for a in x:
                flatten(x[a])
        elif type(x) is list:
            for a in x:
                flatten(a)
        else:
            out.append(str(x))
    flatten(y)
    return " ".join(out)
