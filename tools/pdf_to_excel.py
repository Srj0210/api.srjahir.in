import pdfplumber
import pandas as pd
import os


def pdf_to_excel(input_pdf_path: str, output_excel_path: str):
    """
    Convert PDF tables to Excel (.xlsx)

    Strategy:
    - Uses pdfplumber with LINE-BASED (lattice) table detection
    - Best for invoices, reports, statements, generated PDFs
    - Render safe (no Java, no OCR, no camelot)
    """

    all_tables = []

    with pdfplumber.open(input_pdf_path) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):

            # 🔑 IMPORTANT: lattice-style table detection
            tables = page.extract_tables({
                "vertical_strategy": "lines",
                "horizontal_strategy": "lines",
                "intersection_tolerance": 5,
            })

            if not tables:
                continue

            for table in tables:
                if not table or len(table) < 2:
                    continue

                # First row = header, rest = data
                df = pd.DataFrame(table[1:], columns=table[0])

                # Optional: keep page reference
                df["__page__"] = page_number

                all_tables.append(df)

    if not all_tables:
        raise RuntimeError("No tables found in PDF")

    final_df = pd.concat(all_tables, ignore_index=True)

    # Save to Excel
    final_df.to_excel(output_excel_path, index=False)

    return output_excel_path