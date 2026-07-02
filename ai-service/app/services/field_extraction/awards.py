from app.models.document import Document
from .base import BaseFieldExtractor


class AwardsExtractor(BaseFieldExtractor):
    field_name = "awards"

    def extract(self, document: Document) -> None:
        section_text = document.get_section(self.field_name)
        if not section_text.strip():
            document.resume.awards = []
            return

        awards = [
            line.strip("-• ").strip()
            for line in section_text.splitlines()
            if line.strip()
        ]

        document.resume.awards = awards
