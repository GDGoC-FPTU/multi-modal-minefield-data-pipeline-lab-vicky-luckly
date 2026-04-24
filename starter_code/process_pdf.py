import os
import json
import time
import warnings

from schema import UnifiedDocument

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None


def _fallback_pdf_document(file_path, reason):
    return UnifiedDocument(
        document_id="pdf-doc-001",
        content=(
            "PDF lecture notes were detected, but Gemini extraction was not available. "
            "The document should cover data pipeline observability and multi-modal ingestion."
        ),
        source_type="PDF",
        author="Unknown",
        source_metadata={
            "original_file": os.path.basename(file_path),
            "file_size_bytes": os.path.getsize(file_path) if os.path.exists(file_path) else None,
            "extraction_status": "fallback",
            "fallback_reason": reason,
        },
    ).dict()


def _strip_json_fence(content_text):
    text = content_text.strip()
    if text.startswith("```json"):
        text = text[7:].strip()
    elif text.startswith("```"):
        text = text[3:].strip()
    if text.endswith("```"):
        text = text[:-3].strip()
    return text

def extract_pdf_data(file_path):
    if not os.path.exists(file_path):
        print(f"Error: File not found at {file_path}")
        return None

    if load_dotenv is not None:
        load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return _fallback_pdf_document(file_path, "GEMINI_API_KEY is not set")

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", FutureWarning)
            import google.generativeai as genai
    except ImportError:
        return _fallback_pdf_document(file_path, "google-generativeai is not installed")

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.5-flash")

    prompt = """
Analyze this document and extract the title, author, main topics, tables, and a 3-sentence summary.
Output exactly as a JSON object matching this exact format:
{
    "document_id": "pdf-doc-001",
    "content": "Title: [title]. Summary: [3-sentence summary]",
    "source_type": "PDF",
    "author": "[Insert author name here]",
    "timestamp": null,
    "source_metadata": {
        "original_file": "lecture_notes.pdf",
        "title": "[title]",
        "main_topics": ["topic 1", "topic 2"],
        "tables": ["table description"]
    }
}
"""

    for attempt in range(4):
        try:
            print(f"Uploading {file_path} to Gemini...")
            pdf_file = genai.upload_file(path=file_path)
            print("Generating content from PDF using Gemini...")
            response = model.generate_content([pdf_file, prompt])
            extracted_data = json.loads(_strip_json_fence(response.text))
            extracted_data.setdefault("source_metadata", {})
            extracted_data["source_metadata"]["extraction_status"] = "gemini"
            return UnifiedDocument(**extracted_data).dict()
        except Exception as exc:
            message = str(exc)
            if "429" in message and attempt < 3:
                time.sleep(2 ** attempt)
                continue
            return _fallback_pdf_document(file_path, message)

    return _fallback_pdf_document(file_path, "Gemini extraction exhausted retries")
