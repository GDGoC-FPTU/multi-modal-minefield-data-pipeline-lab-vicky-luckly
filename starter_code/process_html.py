from bs4 import BeautifulSoup

from schema import UnifiedDocument

# ==========================================
# ROLE 2: ETL/ELT BUILDER
# ==========================================
# Task: Extract product data from the HTML table, ignoring boilerplate.

def _parse_price(price_text):
    normalized = price_text.strip().lower()
    if normalized in {"n/a", "na", "liên hệ", "lien he"}:
        return None
    digits = "".join(ch for ch in price_text if ch.isdigit())
    return int(digits) if digits else None


def _parse_rating(rating_text):
    if "/" not in rating_text:
        return None
    return float(rating_text.split("/", 1)[0])


def parse_html_catalog(file_path):
    # --- FILE READING (Handled for students) ---
    with open(file_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')
    # ------------------------------------------

    table = soup.find("table", id="main-catalog")
    if table is None:
        return []

    documents = []
    for row in table.select("tbody tr"):
        cells = [cell.get_text(strip=True) for cell in row.find_all("td")]
        if len(cells) != 6:
            continue

        product_id, product_name, category, price_text, stock_text, rating_text = cells
        price_vnd = _parse_price(price_text)
        stock_quantity = int(stock_text)
        rating = _parse_rating(rating_text)
        price_phrase = f"{price_vnd} VND" if price_vnd is not None else "unavailable price"

        document = UnifiedDocument(
            document_id=f"html-product-{product_id.lower()}",
            content=(
                f"Catalog product {product_id}: {product_name} belongs to {category}, "
                f"listed at {price_phrase}, with stock quantity {stock_quantity}."
            ),
            source_type="HTML",
            source_metadata={
                "product_id": product_id,
                "product_name": product_name,
                "category": category,
                "price_vnd": price_vnd,
                "stock_quantity": stock_quantity,
                "rating": rating,
                "raw_price": price_text,
                "raw_rating": rating_text,
            },
        )
        documents.append(document.dict())

    return documents

