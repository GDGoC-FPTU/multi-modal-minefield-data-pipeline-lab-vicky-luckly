import pandas as pd
from datetime import datetime

from schema import UnifiedDocument

# ==========================================
# ROLE 2: ETL/ELT BUILDER
# ==========================================
# Task: Process sales records, handling type traps and duplicates.

PRICE_WORDS = {
    "five dollars": 5.0,
}


def _clean_price(value):
    if pd.isna(value):
        return None

    text = str(value).strip()
    if not text:
        return None

    lowered = text.lower()
    if lowered in {"n/a", "na", "null", "none", "lien he", "liên hệ"}:
        return None
    if lowered in PRICE_WORDS:
        return PRICE_WORDS[lowered]

    cleaned = (
        text.replace("$", "")
        .replace(",", "")
        .replace("VND", "")
        .replace("USD", "")
        .strip()
    )
    return float(cleaned)


def _clean_date(value):
    text = str(value).strip()
    text = pd.Series([text]).str.replace(r"(\d+)(st|nd|rd|th)", r"\1", regex=True).iloc[0]
    formats = ["%Y-%m-%d", "%d/%m/%Y", "%B %d %Y", "%d-%m-%Y", "%Y/%m/%d", "%d %b %Y"]
    for date_format in formats:
        try:
            return datetime.strptime(text, date_format).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


def _clean_int(value):
    if pd.isna(value):
        return None
    return int(value)


def _is_missing(value):
    return value is None or pd.isna(value)


def process_sales_csv(file_path):
    # --- FILE READING (Handled for students) ---
    df = pd.read_csv(file_path)
    # ------------------------------------------

    df = df.drop_duplicates(subset=["id"], keep="first").copy()
    df["clean_price"] = df["price"].apply(_clean_price)
    df["clean_date"] = df["date_of_sale"].apply(_clean_date)
    df["clean_stock_quantity"] = df["stock_quantity"].apply(_clean_int)

    documents = []
    for _, row in df.iterrows():
        clean_price = None if _is_missing(row["clean_price"]) else float(row["clean_price"])
        clean_date = None if _is_missing(row["clean_date"]) else row["clean_date"]
        clean_stock_quantity = None if _is_missing(row["clean_stock_quantity"]) else int(row["clean_stock_quantity"])
        price_text = (
            f"{clean_price} {row['currency']}"
            if clean_price is not None
            else "unavailable price"
        )
        sale_date = clean_date or "unknown date"
        content = (
            f"Sale record {row['id']}: {row['product_name']} in {row['category']} "
            f"was sold for {price_text} on {sale_date} by seller {row['seller_id']}."
        )

        document = UnifiedDocument(
            document_id=f"csv-sale-{int(row['id']):03d}",
            content=content,
            source_type="CSV",
            timestamp=f"{clean_date}T00:00:00" if clean_date else None,
            source_metadata={
                "raw_id": int(row["id"]),
                "product_name": row["product_name"],
                "category": row["category"],
                "price": clean_price,
                "currency": row["currency"],
                "date_of_sale": clean_date,
                "seller_id": row["seller_id"],
                "stock_quantity": clean_stock_quantity,
                "raw_price": None if pd.isna(row["price"]) else str(row["price"]),
            },
        )
        documents.append(document.dict())

    return documents

