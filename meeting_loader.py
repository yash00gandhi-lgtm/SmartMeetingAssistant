"""
meeting_loader.py
-----------------
Loads meeting notes from either raw text or a PDF file.
"""

from langchain_community.document_loaders import PyPDFLoader


def load_from_pdf(file_path: str) -> str:
    """
    Read a PDF using PyPDFLoader and return the full meeting text
    as a single string.
    """
    loader = PyPDFLoader(file_path)
    pages = loader.load()
    return "\n\n".join(p.page_content for p in pages).strip()


def load_from_text(text: str) -> str:
    """For raw text input, just clean and return it."""
    return text.strip()
