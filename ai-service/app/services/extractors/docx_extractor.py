from docx import Document

from .base import BaseExtractor


class DOCXExtractor(BaseExtractor):

    def extract(self, file_path: str) -> str:

        document = Document(file_path)

        return "\n".join(
            paragraph.text
            for paragraph in document.paragraphs
        )