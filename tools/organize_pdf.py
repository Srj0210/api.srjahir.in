from PyPDF2 import PdfReader, PdfWriter

def organize_pdf(input_path, output_path, order):
    reader = PdfReader(input_path)
    writer = PdfWriter()

    for index in order:
        writer.add_page(reader.pages[index])

    with open(output_path, "wb") as f:
        writer.write(f)
