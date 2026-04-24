import json
import time
import os
from collections.abc import Iterable

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

def _as_document_list(result):
    if result is None:
        return []
    if isinstance(result, dict):
        return [result]
    if isinstance(result, Iterable) and not isinstance(result, (str, bytes)):
        return list(result)
    return []


def _serialize_document(document):
    model = UnifiedDocument(**document)
    if hasattr(model, "model_dump"):
        return model.model_dump(mode="json")
    return json.loads(model.json())


def _ingest_source(source_name, processor, file_path):
    print(f"Processing {source_name}: {os.path.basename(file_path)}")
    try:
        return _as_document_list(processor(file_path))
    except Exception as exc:
        print(f"[WARN] {source_name} failed: {exc}")
        return []


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

    pipeline_steps = [
        ("PDF", extract_pdf_data, pdf_path),
        ("Transcript", clean_transcript, trans_path),
        ("HTML", parse_html_catalog, html_path),
        ("CSV", process_sales_csv, csv_path),
        ("Legacy Code", extract_logic_from_code, code_path),
    ]

    for source_name, processor, file_path in pipeline_steps:
        for document in _ingest_source(source_name, processor, file_path):
            try:
                normalized = _serialize_document(document)
            except Exception as exc:
                print(f"[WARN] Invalid document from {source_name}: {exc}")
                continue

            if run_quality_gate(normalized):
                final_kb.append(normalized)
            else:
                print(f"[INFO] Quality gate rejected {normalized.get('document_id')}")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(final_kb, f, ensure_ascii=False, indent=2)

    end_time = time.time()
    print(f"Pipeline finished in {end_time - start_time:.2f} seconds.")
    print(f"Total valid documents stored: {len(final_kb)}")
    print(f"Output written to: {output_path}")


if __name__ == "__main__":
    main()
