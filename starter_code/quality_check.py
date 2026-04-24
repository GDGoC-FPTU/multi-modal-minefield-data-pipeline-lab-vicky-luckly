# ==========================================
# ROLE 3: OBSERVABILITY & QA ENGINEER
# ==========================================
# Task: Implement quality gates to reject corrupt data or logic discrepancies.

TOXIC_STRINGS = [
    "Null pointer exception",
    "Traceback",
    "undefined is not a function",
    "segmentation fault",
]


def _is_missing_number(value):
    return value is None or str(value).lower() == "nan"


def run_quality_gate(document_dict):
    content = str(document_dict.get("content", "")).strip()
    if len(content) < 20:
        return False

    lowered = content.lower()
    if any(toxic.lower() in lowered for toxic in TOXIC_STRINGS):
        return False

    metadata = document_dict.setdefault("source_metadata", {})

    price = metadata.get("price", metadata.get("price_vnd"))
    if not _is_missing_number(price) and float(price) < 0:
        return False

    stock_quantity = metadata.get("stock_quantity")
    if not _is_missing_number(stock_quantity) and int(stock_quantity) < 0:
        return False

    if metadata.get("tax_discrepancy"):
        warnings = metadata.setdefault("quality_warnings", [])
        warnings.append(metadata["tax_discrepancy"]["message"])

    return True
