import google.generativeai as genai
import os
import json
import re
import time
from dotenv import load_dotenv

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)


def _is_rate_limit_error(error):
    error_message = str(error).lower()
    return "429" in error_message or "rate limit" in error_message or "quota" in error_message


def _parse_json_response(raw_text):
    text = (raw_text or "").strip()
    if not text:
        raise ValueError("Gemini returned an empty response.")

    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?", "", text, flags=re.IGNORECASE).strip()
        if text.endswith("```"):
            text = text[:-3].strip()

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        text = text[start:end + 1]

    return json.loads(text)


def _fallback_document(file_path, reason):
    file_name = os.path.basename(file_path)
    return {
        "document_id": "pdf-doc-001",
        "content": f"PDF extraction fallback for {file_name}. Reason: {reason}",
        "source_type": "PDF",
        "author": "Unknown",
        "timestamp": None,
        "source_metadata": {
            "original_file": file_name,
            "extraction_status": "fallback",
        },
    }


def _generate_with_backoff(model, payload, retries=5, base_delay=1.0):
    last_error = None
    for attempt in range(retries):
        try:
            return model.generate_content(payload)
        except Exception as error:
            last_error = error
            if not _is_rate_limit_error(error) or attempt == retries - 1:
                raise
            wait_seconds = base_delay * (2 ** attempt)
            print(f"Rate limit hit, retrying in {wait_seconds:.1f}s...")
            time.sleep(wait_seconds)
    raise last_error

def extract_pdf_data(file_path):
    if not os.path.exists(file_path):
        print(f"Error: File not found at {file_path}")
        return None

    if not GEMINI_API_KEY:
        return _fallback_document(file_path, "missing GEMINI_API_KEY")

    model = genai.GenerativeModel('gemini-2.5-flash')

    print(f"Uploading {file_path} to Gemini...")
    try:
        pdf_file = genai.upload_file(path=file_path)
    except Exception as e:
        print(f"Failed to upload file to Gemini: {e}")
        return _fallback_document(file_path, f"upload_failed: {e}")

    prompt = """
You are extracting structured metadata from a lecture PDF.
Return ONLY a JSON object in this exact shape:
{
  "title": "string",
  "author": "string or Unknown",
  "summary": "exactly 3 sentences",
  "main_topics": ["topic 1", "topic 2"],
  "tables": [
    {
      "table_name": "string",
      "key_values": ["fact 1", "fact 2"]
    }
  ]
}
"""

    print("Generating content from PDF using Gemini...")
    try:
        response = _generate_with_backoff(model, [pdf_file, prompt])
        extracted = _parse_json_response(response.text)
    except Exception as e:
        print(f"Gemini extraction failed: {e}")
        return _fallback_document(file_path, f"generation_failed: {e}")

    title = str(extracted.get("title", "Untitled Document")).strip() or "Untitled Document"
    author = str(extracted.get("author", "Unknown")).strip() or "Unknown"
    summary = str(extracted.get("summary", "No summary extracted.")).strip() or "No summary extracted."
    topics = extracted.get("main_topics") if isinstance(extracted.get("main_topics"), list) else []
    tables = extracted.get("tables") if isinstance(extracted.get("tables"), list) else []

    content_parts = [f"Title: {title}", f"Summary: {summary}"]
    if topics:
        content_parts.append("Main topics: " + ", ".join(str(topic) for topic in topics))
    if tables:
        content_parts.append(f"Detected tables: {len(tables)}")

    return {
        "document_id": "pdf-doc-001",
        "content": " ".join(content_parts),
        "source_type": "PDF",
        "author": author,
        "timestamp": None,
        "source_metadata": {
            "original_file": os.path.basename(file_path),
            "title": title,
            "main_topics": topics,
            "tables": tables,
            "extraction_status": "success",
        },
    }
