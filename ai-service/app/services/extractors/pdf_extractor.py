import fitz

from .base import BaseExtractor


class PDFExtractor(BaseExtractor):

    def extract(self, file_path: str) -> str:

        document = fitz.open(file_path)

        text = ""

        for page in document:
            text += page.get_text()

        document.close()

        return text