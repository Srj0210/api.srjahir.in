from pypdf import PdfReader, PdfWriter

def remove_pages(input_path, output_path, pages_to_delete):
    reader = PdfReader(input_path)
    writer = PdfWriter()

    for index, page in enumerate(reader.pages, start=1):
        if index not in pages_to_delete:
            writer.add_page(page)

    with open(output_path, "wb") as f:
        writer.write(f)
