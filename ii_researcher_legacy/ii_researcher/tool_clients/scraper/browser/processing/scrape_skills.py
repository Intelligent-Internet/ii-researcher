from langchain_community.document_loaders import PyMuPDFLoader


def scrape_pdf_with_pymupdf(url) -> str:
    """Scrape a pdf with pymupdf

    Args:
        url (str): The url of the pdf to scrape

    Returns:
        str: The text scraped from the pdf
    """
    loader = PyMuPDFLoader(url)
    doc = loader.load()
    return str(doc)
