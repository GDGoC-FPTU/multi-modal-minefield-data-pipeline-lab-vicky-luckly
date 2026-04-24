# ==========================================
# ROLE 3: OBSERVABILITY & QA ENGINEER
# ==========================================
# Task: Implement quality gates to reject corrupt data or logic discrepancies.

TOXIC_STRINGS = (
    'null pointer exception',
    'segmentation fault',
    'traceback (most recent call last)',
    'fatal error',
)


def _contains_toxic_content(content):
    lowered = content.lower()
    return any(token in lowered for token in TOXIC_STRINGS)


def _has_logic_discrepancy(document_dict):
    source_metadata = document_dict.get('source_metadata', {}) or {}
    discrepancies = source_metadata.get('detected_discrepancies') or []
    return len(discrepancies) > 0

def run_quality_gate(document_dict):
    content = str(document_dict.get('content', '')).strip()

    if len(content) < 20:
        return False

    if _contains_toxic_content(content):
        return False

    # Reject documents that carry explicit business-logic inconsistencies.
    if _has_logic_discrepancy(document_dict):
        return False

    # Return True if pass, False if fail.
    return True
