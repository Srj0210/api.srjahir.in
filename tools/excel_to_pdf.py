import os
import pdfplumber
import pandas as pd
import tempfile
from tools.ocr_pdf import run_ocr


def pdf_to_excel(input_pdf_path: str, output_excel_path: str):
    """
    Smart PDF → Excel
    1️⃣ Try table extraction
    2️⃣ If no tables → create NOTICE Excel (no failure)
    3️⃣ Never crash frontend
    """

    all_tables = []

    # ---------- STEP 1: Try normal table extraction ----------
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

        # ✅ Tables found → save Excel
        if all_tables:
            final_df = pd.concat(all_tables, ignore_index=True)
            final_df.to_excel(output_excel_path, index=False)
            return output_excel_path

    except Exception:
        pass  # silently move to fallback

    # ---------- STEP 2: FALLBACK (NO TABLE FOUND) ----------
    notice_df = pd.DataFrame(
        [
            "No structured tables found in this PDF.",
            "This PDF may be scanned or text-based without table borders.",
            "Tip: Use OCR tool first, then convert OCR output to Excel."
        ],
        columns=["Notice"]
    )

    notice_df.to_excel(output_excel_path, index=False)
    return output_excel_path
