from app.models.document import Document
from app.services.section_detection.keywords import SECTION_KEYWORDS
from app.services.section_detection.utils import normalize
from .base import PipelineStage


class HeaderStage(PipelineStage):

    def process(self, document: Document) -> Document:
        lines = document.cleaned_text.splitlines()
        header_lines = []

        for line in lines:
            cleaned = normalize(line)
            is_heading = False
            for keywords in SECTION_KEYWORDS.values():
                if cleaned in keywords:
                    is_heading = True
                    break
            if is_heading:
                break
            header_lines.append(line)

        document.header = "\n".join(header_lines).strip()
        return document
