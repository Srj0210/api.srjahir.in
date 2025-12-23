import pdfplumber
import pandas as pd
import os
import tempfile

from tools.ocr_pdf import run_ocr


def extract_tables(pdf_path):
    all_tables = []

    with pdfplumber.open(pdf_path) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):

            tables = page.extract_tables({
                "vertical_strategy": "lines",
                "horizontal_strategy": "lines",
                "intersection_tolerance": 5,
            })

            for table in tables:
                if not table or len(table) < 2:
                    continue

                df = pd.DataFrame(table[1:], columns=table[0])
                df["__page__"] = page_number
                all_tables.append(df)

    return all_tables


def pdf_to_excel(input_pdf_path: str, output_excel_path: str):
    """
    PDF → Excel (Smart Mode)

    1️⃣ Try direct table extraction
    2️⃣ If no tables → OCR → retry
    """

    # -------- STEP 1: NORMAL TRY --------
    tables = extract_tables(input_pdf_path)

    # -------- STEP 2: OCR FALLBACK --------
    if not tables:
        with tempfile.TemporaryDirectory() as tmp:
            ocr_pdf_path = os.path.join(tmp, "ocr.pdf")

            # OCR → searchable PDF
            run_ocr(input_pdf_path, ocr_pdf_path, output_type="pdf")

            # Retry extraction
            tables = extract_tables(ocr_pdf_path)

    if not tables:
        raise RuntimeError("No tables found even after OCR")

    final_df = pd.concat(tables, ignore_index=True)
    final_df.to_excel(output_excel_path, index=False)

    return output_excel_path