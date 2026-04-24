import pandas as pd
import re
from datetime import datetime

# ==========================================
# ROLE 2: ETL/ELT BUILDER
# ==========================================
# Task: Process sales records, handling type traps and duplicates.

WORD_TO_NUMBER = {
    "zero": 0,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
}


def _normalize_price(raw_value):
    if pd.isna(raw_value):
        return None

    value = str(raw_value).strip()
    if not value:
        return None

    if value.upper() in {"N/A", "NULL", "NONE"}:
        return None
    if value.lower() in {"lien he", "liên hệ"}:
        return None

    cleaned = value.replace(",", "")
    cleaned = re.sub(r"[^\d.\-]", "", cleaned)
    if cleaned and cleaned not in {"-", ".", "-."}:
        try:
            return float(cleaned)
        except ValueError:
            pass

    # Fallback for text like "five dollars"
    tokens = re.findall(r"[a-z]+", value.lower())
    if not tokens:
        return None

    total = 0
    found_number = False
    for token in tokens:
        if token in WORD_TO_NUMBER:
            total += WORD_TO_NUMBER[token]
            found_number = True

    if not found_number:
        return None
    return float(total)


def _normalize_date(raw_value):
    if pd.isna(raw_value):
        return None

    value = str(raw_value).strip()
    if not value:
        return None

    value = re.sub(r"(\d+)(st|nd|rd|th)", r"\1", value, flags=re.IGNORECASE)

    known_formats = [
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%Y/%m/%d",
        "%d %b %Y",
        "%B %d %Y",
    ]

    for fmt in known_formats:
        try:
            return datetime.strptime(value, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue

    parsed = pd.to_datetime(value, errors="coerce", dayfirst=True)
    if pd.isna(parsed):
        parsed = pd.to_datetime(value, errors="coerce", dayfirst=False)
    if pd.isna(parsed):
        return None

    return parsed.strftime("%Y-%m-%d")


def _safe_int(raw_value):
    if pd.isna(raw_value):
        return None
    try:
        return int(float(raw_value))
    except (TypeError, ValueError):
        return None

def process_sales_csv(file_path):
    # --- FILE READING (Handled for students) ---
    df = pd.read_csv(file_path)
    # ------------------------------------------

    dedup_df = df.drop_duplicates(subset=["id"], keep="first").copy()
    documents = []

    for _, row in dedup_df.iterrows():
        row_id = str(row.get("id", "unknown")).strip()
        if row_id.endswith(".0"):
            row_id = row_id[:-2]

        product_name = str(row.get("product_name", "Unknown product")).strip()
        category = str(row.get("category", "Unknown category")).strip()
        raw_price = row.get("price")
        normalized_price = _normalize_price(raw_price)
        currency = str(row.get("currency", "UNKNOWN")).strip() or "UNKNOWN"
        normalized_date = _normalize_date(row.get("date_of_sale"))
        seller_id = str(row.get("seller_id", "Unknown")).strip() or "Unknown"
        stock_quantity = _safe_int(row.get("stock_quantity"))

        content = (
            f"Sale record for {product_name} ({category}). "
            f"Raw price: {raw_price}; normalized price: {normalized_price}."
        )

        documents.append(
            {
                "document_id": f"csv-{row_id}",
                "content": content,
                "source_type": "CSV",
                "author": seller_id,
                "timestamp": f"{normalized_date}T00:00:00" if normalized_date else None,
                "source_metadata": {
                    "product_name": product_name,
                    "category": category,
                    "raw_price": None if pd.isna(raw_price) else str(raw_price),
                    "normalized_price": normalized_price,
                    "currency": currency,
                    "date_of_sale": normalized_date,
                    "seller_id": seller_id,
                    "stock_quantity": stock_quantity,
                },
            }
        )

    return documents

