import json
import time
import os

# Robust path handling
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DATA_DIR = os.path.join(os.path.dirname(SCRIPT_DIR), "raw_data")


# Import role-specific modules
from schema import UnifiedDocument
from process_pdf import extract_pdf_data
from process_transcript import clean_transcript
from process_html import parse_html_catalog
from process_csv import process_sales_csv
from process_legacy_code import extract_logic_from_code
from quality_check import run_quality_gate

# ==========================================
# ROLE 4: DEVOPS & INTEGRATION SPECIALIST
# ==========================================
# Task: Orchestrate the ingestion pipeline and handle errors/SLA.


def _to_json_document(unified_document):
    if hasattr(unified_document, "model_dump"):
        return unified_document.model_dump(mode="json")
    return json.loads(unified_document.json())


def _validate_and_collect(raw_output, final_kb, source_name):
    if raw_output is None:
        print(f"{source_name}: no data returned.")
        return

    candidates = raw_output if isinstance(raw_output, list) else [raw_output]
    for candidate in candidates:
        if not candidate:
            continue

        try:
            if hasattr(UnifiedDocument, "model_validate"):
                validated = UnifiedDocument.model_validate(candidate)
            else:
                validated = UnifiedDocument.parse_obj(candidate)
        except Exception as error:
            print(f"{source_name}: schema validation failed -> {error}")
            continue

        document_dict = _to_json_document(validated)
        if run_quality_gate(document_dict):
            final_kb.append(document_dict)
        else:
            print(f"{source_name}: quality gate rejected {document_dict.get('document_id', 'unknown-id')}")

def main():
    start_time = time.time()
    final_kb = []
    
    # --- FILE PATH SETUP (Handled for students) ---
    pdf_path = os.path.join(RAW_DATA_DIR, "lecture_notes.pdf")
    trans_path = os.path.join(RAW_DATA_DIR, "demo_transcript.txt")
    html_path = os.path.join(RAW_DATA_DIR, "product_catalog.html")
    csv_path = os.path.join(RAW_DATA_DIR, "sales_records.csv")
    code_path = os.path.join(RAW_DATA_DIR, "legacy_pipeline.py")
    
    output_path = os.path.join(os.path.dirname(SCRIPT_DIR), "processed_knowledge_base.json")
    # ----------------------------------------------

    source_outputs = [
        ("PDF", extract_pdf_data(pdf_path)),
        ("Transcript", clean_transcript(trans_path)),
        ("HTML", parse_html_catalog(html_path)),
        ("CSV", process_sales_csv(csv_path)),
        ("LegacyCode", extract_logic_from_code(code_path)),
    ]

    for source_name, output in source_outputs:
        _validate_and_collect(output, final_kb, source_name)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(final_kb, f, ensure_ascii=False, indent=2)

    print(f"Knowledge base written to: {output_path}")

    end_time = time.time()
    print(f"Pipeline finished in {end_time - start_time:.2f} seconds.")
    print(f"Total valid documents stored: {len(final_kb)}")


if __name__ == "__main__":
    main()
