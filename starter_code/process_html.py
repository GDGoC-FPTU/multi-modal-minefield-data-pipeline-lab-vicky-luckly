from bs4 import BeautifulSoup
import re

# ==========================================
# ROLE 2: ETL/ELT BUILDER
# ==========================================
# Task: Extract product data from the HTML table, ignoring boilerplate.


def _parse_price_vnd(raw_price):
    if raw_price is None:
        return None

    value = raw_price.strip()
    if not value:
        return None

    lowered = value.lower()
    if lowered in {"n/a", "null", "lien he", "liên hệ"}:
        return None

    cleaned = re.sub(r"[^\d\-]", "", value)
    if not cleaned or cleaned == "-":
        return None

    try:
        return int(cleaned)
    except ValueError:
        return None


def _safe_int(raw_value):
    try:
        return int(str(raw_value).strip())
    except (TypeError, ValueError):
        return None

def parse_html_catalog(file_path):
    # --- FILE READING (Handled for students) ---
    with open(file_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')
    # ------------------------------------------

    table = soup.find('table', id='main-catalog')
    if table is None:
        return []

    table_body = table.find('tbody')
    if table_body is None:
        return []

    documents = []

    for row in table_body.find_all('tr'):
        columns = [cell.get_text(' ', strip=True) for cell in row.find_all('td')]
        if len(columns) < 6:
            continue

        product_id, product_name, category, raw_price, raw_stock, rating = columns[:6]
        normalized_price = _parse_price_vnd(raw_price)
        stock_quantity = _safe_int(raw_stock)

        content = (
            f"Catalog item {product_id}: {product_name} in category {category}. "
            f"Listed price text: {raw_price}."
        )

        documents.append(
            {
                'document_id': f'html-{product_id}',
                'content': content,
                'source_type': 'HTML',
                'author': 'VinShop Catalog',
                'timestamp': None,
                'source_metadata': {
                    'product_id': product_id,
                    'product_name': product_name,
                    'category': category,
                    'raw_price': raw_price,
                    'normalized_price_vnd': normalized_price,
                    'stock_quantity': stock_quantity,
                    'rating': rating,
                },
            }
        )

    return documents

