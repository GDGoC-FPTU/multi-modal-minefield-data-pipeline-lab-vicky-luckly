import ast
import re
import tokenize
from io import StringIO

from schema import UnifiedDocument

# ==========================================
# ROLE 2: ETL/ELT BUILDER
# ==========================================
# Task: Extract docstrings and comments from legacy Python code.

def _extract_comments(source_code):
    comments = []
    tokens = tokenize.generate_tokens(StringIO(source_code).readline)
    for token_type, token_text, _, _, _ in tokens:
        if token_type == tokenize.COMMENT:
            comments.append(token_text.lstrip("#").strip())
    return comments


def _find_tax_discrepancy(source_code, comments):
    comment_text = " ".join(comments)
    mentioned_rates = [int(rate) for rate in re.findall(r"(\d+)%", comment_text)]
    code_match = re.search(r"tax_rate\s*=\s*(0\.\d+)", source_code)
    if not mentioned_rates or not code_match:
        return None

    code_rate = int(round(float(code_match.group(1)) * 100))
    conflicting_rates = sorted({rate for rate in mentioned_rates if rate != code_rate})
    if conflicting_rates:
        return {
            "comment_rates_percent": mentioned_rates,
            "code_rate_percent": code_rate,
            "conflicting_comment_rates_percent": conflicting_rates,
            "message": "Tax-rate comment and implementation disagree.",
        }
    return None


def extract_logic_from_code(file_path):
    # --- FILE READING (Handled for students) ---
    with open(file_path, 'r', encoding='utf-8') as f:
        source_code = f.read()
    # ------------------------------------------

    tree = ast.parse(source_code)
    module_docstring = ast.get_docstring(tree)
    function_docstrings = {}

    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            docstring = ast.get_docstring(node)
            if docstring:
                function_docstrings[node.name] = docstring

    comments = _extract_comments(source_code)
    business_rules = []
    for name, docstring in function_docstrings.items():
        if "Business Logic Rule" in docstring:
            business_rules.append({"function": name, "rule": docstring})

    tax_discrepancy = _find_tax_discrepancy(source_code, comments)
    content_parts = []
    if module_docstring:
        content_parts.append(module_docstring)
    content_parts.extend(f"{name}: {doc}" for name, doc in function_docstrings.items())
    content_parts.extend(comments)

    document = UnifiedDocument(
        document_id="code-legacy-pipeline-001",
        content="\n\n".join(content_parts),
        source_type="Code",
        author="Senior Dev (retired)",
        source_metadata={
            "original_file": "legacy_pipeline.py",
            "function_docstrings": function_docstrings,
            "business_rules": business_rules,
            "comments": comments,
            "tax_discrepancy": tax_discrepancy,
        },
    )

    return document.dict()

