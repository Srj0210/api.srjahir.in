import os
import pdfplumber
import pandas as pd
import tempfile
from tools.ocr_pdf import run_ocr


def pdf_to_excel(input_pdf_path: str, output_excel_path: str):
    """
    Smart PDF → Excel
    1️⃣ Try pdfplumber tables
    2️⃣ If fails → OCR fallback
    """

    all_tables = []

    # ---------- STEP 1: TRY NORMAL TABLE EXTRACTION ----------
    try:
        with pdfplumber.open(input_pdf_path) as pdf:
            for page_number, page in enumerate(pdf.pages, start=1):
                tables = page.extract_tables()

                for table in tables:
                    if not table or len(table) < 2:
                        continue

                    df = pd.DataFrame(table[1:], columns=table[0])
                    df["__page__"] = page_number
                    all_tables.append(df)

        if all_tables:
            final_df = pd.concat(all_tables, ignore_index=True)
            final_df.to_excel(output_excel_path, index=False)
            return output_excel_path

    except Exception:
        pass  # silently fallback to OCR


    # ---------- STEP 2: OCR FALLBACK ----------
    with tempfile.TemporaryDirectory() as tmp:
        ocr_text_path = os.path.join(tmp, "ocr.txt")

        # OCR PDF → TEXT
        run_ocr(input_pdf_path, ocr_text_path, output_type="text")

        # Read OCR text
        with open(ocr_text_path, "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f.readlines() if l.strip()]

        if not lines:
            raise RuntimeError("OCR failed to extract text")

        # Convert OCR text to Excel (simple rows)
        df = pd.DataFrame(lines, columns=["Extracted_Text"])
        df.to_excel(output_excel_path, index=False)

        return output_excel_path
