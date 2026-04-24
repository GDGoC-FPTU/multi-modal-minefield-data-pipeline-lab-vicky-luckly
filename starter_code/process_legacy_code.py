import ast
import re

# ==========================================
# ROLE 2: ETL/ELT BUILDER
# ==========================================
# Task: Extract docstrings and comments from legacy Python code.


def _extract_business_rule_comments(source_code):
    comments = []
    for line in source_code.splitlines():
        stripped = line.strip()
        if stripped.startswith('#') and (
            'Business Logic Rule' in stripped or 'WARNING' in stripped or 'IMPORTANT' in stripped
        ):
            comments.append(stripped.lstrip('# ').strip())
    return comments


def _extract_tax_discrepancy(source_code):
    comment_match = re.search(r"does\s+(\d+)%", source_code, flags=re.IGNORECASE)
    code_match = re.search(r"tax_rate\s*=\s*([0-9]*\.?[0-9]+)", source_code)

    if not comment_match or not code_match:
        return []

    comment_rate = float(comment_match.group(1))
    raw_code_rate = float(code_match.group(1))
    code_rate = raw_code_rate * 100 if raw_code_rate <= 1 else raw_code_rate

    if abs(comment_rate - code_rate) < 1e-9:
        return []

    return [
        {
            'type': 'tax_rate_comment_mismatch',
            'comment_rate_percent': comment_rate,
            'code_rate_percent': code_rate,
        }
    ]

def extract_logic_from_code(file_path):
    # --- FILE READING (Handled for students) ---
    with open(file_path, 'r', encoding='utf-8') as f:
        source_code = f.read()
    # ------------------------------------------

    tree = ast.parse(source_code)
    module_docstring = ast.get_docstring(tree) or ""

    function_docstrings = {}
    function_names = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            function_names.append(node.name)
            docstring = ast.get_docstring(node)
            if docstring:
                function_docstrings[node.name] = docstring.strip()

    business_rule_comments = _extract_business_rule_comments(source_code)
    discrepancies = _extract_tax_discrepancy(source_code)

    author_match = re.search(r"Author:\s*(.+)", module_docstring)
    author = author_match.group(1).strip() if author_match else 'Unknown'

    content = (
        f"Legacy module analysis for functions: {', '.join(function_names)}. "
        f"Extracted {len(function_docstrings)} function docstrings and "
        f"{len(business_rule_comments)} business-rule comments."
    )

    return {
        'document_id': 'code-legacy-001',
        'content': content,
        'source_type': 'Code',
        'author': author,
        'timestamp': None,
        'source_metadata': {
            'module_docstring': module_docstring,
            'function_docstrings': function_docstrings,
            'business_rule_comments': business_rule_comments,
            'detected_discrepancies': discrepancies,
        },
    }

