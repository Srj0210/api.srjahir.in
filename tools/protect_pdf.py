from PyPDF2 import PdfReader, PdfWriter


def protect_pdf(input_pdf_path: str, output_pdf_path: str, password: str):
    """
    Protect PDF with password (AES-128)
    """

    reader = PdfReader(input_pdf_path)
    writer = PdfWriter()

    for page in reader.pages:
        writer.add_page(page)

    # Encrypt PDF
    writer.encrypt(user_password=password, owner_password=password, use_128bit=True)

    with open(output_pdf_path, "wb") as f:
        writer.write(f)