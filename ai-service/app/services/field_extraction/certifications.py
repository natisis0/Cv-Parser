from app.models.document import Document
from app.models.certification import Certification
from .base import BaseFieldExtractor


class CertificationExtractor(BaseFieldExtractor):
    field_name = "certifications"

    def extract(self, document: Document) -> None:
        section_text = document.get_section(self.field_name)
        if not section_text.strip():
            document.resume.certifications = []
            return

        lines = [
            line.strip("-• ").strip()
            for line in section_text.splitlines()
            if line.strip()
        ]

        certs = []
        for line in lines:
            if len(line) > 2:
                certs.append(Certification(name=line))

        document.resume.certifications = certs
