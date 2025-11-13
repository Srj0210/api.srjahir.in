import PyPDF2

def remove_pages(input_path, output_path, pages_to_delete):
    reader = PyPDF2.PdfReader(input_path)
    writer = PyPDF2.PdfWriter()

    for index, page in enumerate(reader.pages, start=1):
        if index not in pages_to_delete:
            writer.add_page(page)

    with open(output_path, "wb") as f:
        writer.write(f)
