import os
import pdfplumber
import pandas as pd
import tempfile
from tools.ocr_pdf import run_ocr


def pdf_to_excel(input_pdf_path: str, output_excel_path: str):
    """
    Smart PDF → Excel Converter

    Logic:
    1️⃣ Try structured table extraction using pdfplumber
    2️⃣ If no tables found → OCR fallback
    3️⃣ If OCR also empty → still generate Excel with Notice
    """

    all_tables = []

    # ===============================
    # STEP 1: TRY NORMAL TABLE EXTRACTION
    # ===============================
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

        # ✅ If tables found → save & return
        if all_tables:
            final_df = pd.concat(all_tables, ignore_index=True)
            final_df.to_excel(output_excel_path, index=False)
            return output_excel_path

    except Exception:
        # silently move to OCR fallback
        pass


    # ===============================
    # STEP 2: OCR FALLBACK (TEXT BASED)
    # ===============================
    with tempfile.TemporaryDirectory() as tmp:
        ocr_text_path = os.path.join(tmp, "ocr.txt")

        # Run OCR → TEXT
        run_ocr(input_pdf_path, ocr_text_path, output_type="text")

        # Read OCR output
        if os.path.exists(ocr_text_path):
            with open(ocr_text_path, "r", encoding="utf-8") as f:
                lines = [line.strip() for line in f.readlines() if line.strip()]
        else:
            lines = []

        # ===============================
        # STEP 3: IF OCR ALSO EMPTY → NOTICE EXCEL
        # ===============================
        if not lines:
            df = pd.DataFrame(
                ["No structured table found. This PDF may be scanned or image-based."],
                columns=["Notice"]
            )
            df.to_excel(output_excel_path, index=False)
            return output_excel_path

        # ===============================
        # STEP 4: OCR TEXT → EXCEL
        # ===============================
        df = pd.DataFrame(lines, columns=["Extracted_Text"])
        df.to_excel(output_excel_path, index=False)
        return output_excel_path