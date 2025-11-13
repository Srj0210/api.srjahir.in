from PyPDF2 import PdfReader, PdfWriter

def organize_pdf(input_path, output_path, order_list):
    reader = PdfReader(input_path)
    writer = PdfWriter()

    for page_num in order_list:
        writer.add_page(reader.pages[page_num - 1])

    with open(output_path, "wb") as f:
        writer.write(f)
