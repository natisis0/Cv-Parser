from pathlib import Path

from .pdf_extractor import PDFExtractor
from .docx_extractor import DOCXExtractor


def get_extractor(file_path: str):

    extension = Path(file_path).suffix.lower()

    if extension == ".pdf":
        return PDFExtractor()

    if extension == ".docx":
        return DOCXExtractor()

    raise ValueError("Unsupported file type")