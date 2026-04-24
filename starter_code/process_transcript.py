import re

from schema import UnifiedDocument

# ==========================================
# ROLE 2: ETL/ELT BUILDER
# ==========================================
# Task: Clean the transcript text and extract key information.

VIETNAMESE_PRICE_PATTERNS = {
    "năm trăm nghìn": 500000,
    "nam tram nghin": 500000,
}


def _clean_text(text):
    text = re.sub(r"\[\d{2}:\d{2}:\d{2}\]", " ", text)
    text = re.sub(r"\[(?:Music starts|Music ends|Music|inaudible|Laughter)\]", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"\[Speaker\s+\d+\]:", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _extract_price_vnd(text):
    numeric_match = re.search(r"(\d[\d,\.]*)\s*VND", text, flags=re.IGNORECASE)
    if numeric_match:
        digits = re.sub(r"[^\d]", "", numeric_match.group(1))
        if digits:
            return int(digits)

    lowered = text.lower()
    for phrase, value in VIETNAMESE_PRICE_PATTERNS.items():
        if phrase in lowered:
            return value

    return None


def clean_transcript(file_path):
    # --- FILE READING (Handled for students) ---
    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()
    # ------------------------------------------

    cleaned_text = _clean_text(text)
    detected_price_vnd = _extract_price_vnd(cleaned_text)

    document = UnifiedDocument(
        document_id="video-transcript-001",
        content=cleaned_text,
        source_type="Video",
        source_metadata={
            "original_file": "demo_transcript.txt",
            "detected_price_vnd": detected_price_vnd,
            "removed_noise_tokens": ["Music", "inaudible", "Laughter"],
        },
    )

    return document.dict()

