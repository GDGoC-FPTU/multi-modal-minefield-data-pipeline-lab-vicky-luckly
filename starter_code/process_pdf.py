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

REQUIRED_RESPONSE_FIELDS = ("title", "author", "summary", "main_topics", "tables")


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


def _require_api_key():
    if GEMINI_API_KEY:
        return
    raise RuntimeError(
        "GEMINI_API_KEY is missing. Create a .env file in project root with "
        "GEMINI_API_KEY=<your_key> or set environment variable before running."
    )


def _normalize_tables(raw_tables):
    if not isinstance(raw_tables, list):
        return []

    normalized = []
    for table in raw_tables:
        if not isinstance(table, dict):
            continue

        table_name = str(table.get("table_name", "")).strip() or "Unnamed table"
        key_values = table.get("key_values", [])
        if not isinstance(key_values, list):
            key_values = []

        clean_values = [str(value).strip() for value in key_values if str(value).strip()]
        normalized.append({"table_name": table_name, "key_values": clean_values})

    return normalized


def _validate_payload(payload):
    if not isinstance(payload, dict):
        raise ValueError("Gemini response is not a JSON object.")

    missing_fields = [field for field in REQUIRED_RESPONSE_FIELDS if field not in payload]
    if missing_fields:
        raise ValueError(f"Gemini response is missing required fields: {missing_fields}")

    summary = str(payload.get("summary", "")).strip()
    if len(summary) < 30:
        raise ValueError("Gemini summary is too short to be useful.")

    topics = payload.get("main_topics")
    if not isinstance(topics, list):
        raise ValueError("main_topics must be a list.")

    for topic in topics:
        if not str(topic).strip():
            raise ValueError("main_topics contains an empty topic.")


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
        raise FileNotFoundError(f"PDF file not found at: {file_path}")

    _require_api_key()

    model = genai.GenerativeModel('gemini-2.5-flash')

    print(f"Uploading {file_path} to Gemini...")
    try:
        pdf_file = genai.upload_file(path=file_path)
    except Exception as error:
        raise RuntimeError(f"Failed to upload PDF to Gemini: {error}") from error

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
        _validate_payload(extracted)
    except Exception as error:
        raise RuntimeError(f"Gemini extraction failed: {error}") from error

    title = str(extracted.get("title", "Untitled Document")).strip() or "Untitled Document"
    author = str(extracted.get("author", "Unknown")).strip() or "Unknown"
    summary = str(extracted.get("summary", "No summary extracted.")).strip() or "No summary extracted."
    topics = [str(topic).strip() for topic in extracted.get("main_topics", []) if str(topic).strip()]
    tables = _normalize_tables(extracted.get("tables", []))

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
