from pypdf import PdfReader


def load_pdf(path):
    reader = PdfReader(path)
    pages = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            pages.append(text)
    full_text = "\n\n".join(pages)
    print(f"Loaded PDF: {len(reader.pages)} pages, {len(full_text)} characters")
    return full_text
