import re

# ==========================================
# ROLE 2: ETL/ELT BUILDER
# ==========================================
# Task: Clean the transcript text and extract key information.


def _remove_noise(text):
    cleaned = re.sub(r"\[\d{2}:\d{2}:\d{2}\]", " ", text)
    cleaned = re.sub(r"\[Speaker\s*\d+\]:", " ", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\[(music starts|music ends|music|inaudible|laughter)\]", " ", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\[[^\]]+\]", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def _extract_numeric_vnd(text):
    match = re.search(r"(\d{1,3}(?:[\.,]\d{3})+|\d+)\s*VND", text, flags=re.IGNORECASE)
    if not match:
        return None

    raw_number = match.group(1).replace(".", "").replace(",", "")
    try:
        return int(raw_number)
    except ValueError:
        return None


def _extract_vietnamese_word_price(text):
    lowered = text.lower()
    phrase_map = {
        "năm trăm nghìn": 500000,
        "mot trieu": 1000000,
        "một triệu": 1000000,
    }
    for phrase, amount in phrase_map.items():
        if phrase in lowered:
            return amount
    return None

def clean_transcript(file_path):
    # --- FILE READING (Handled for students) ---
    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()
    # ------------------------------------------

    cleaned_text = _remove_noise(text)
    numeric_price = _extract_numeric_vnd(text)
    word_price = _extract_vietnamese_word_price(text)

    # Prefer explicit digits when present, fallback to word phrase extraction.
    detected_price = numeric_price if numeric_price is not None else word_price

    return {
        "document_id": "transcript-001",
        "content": cleaned_text,
        "source_type": "Video",
        "author": "Transcript Speaker",
        "timestamp": None,
        "source_metadata": {
            "detected_price_vnd": detected_price,
            "price_from_numeric": numeric_price,
            "price_from_words": word_price,
            "language": "vi",
        },
    }

