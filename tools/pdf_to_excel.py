import pdfplumber
import pandas as pd
import os


def pdf_to_excel(input_pdf_path: str, output_excel_path: str):
    """
    Convert PDF tables to Excel (.xlsx)
    Uses pdfplumber + pandas
    Render safe, no Java, no OCR
    """

    all_tables = []

    with pdfplumber.open(input_pdf_path) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            tables = page.extract_tables()

            for table in tables:
                if not table or len(table) < 2:
                    continue

                df = pd.DataFrame(table[1:], columns=table[0])
                df["__page__"] = page_number
                all_tables.append(df)

    if not all_tables:
        raise RuntimeError("No tables found in PDF")

    final_df = pd.concat(all_tables, ignore_index=True)
    final_df.to_excel(output_excel_path, index=False)

    return output_excel_path