from app.models.document import Document
from app.services.section_detection.detector import detect_sections
from .base import PipelineStage


class SectionDetectionStage(PipelineStage):

    def process(self, document: Document) -> Document:

        sections = detect_sections(document.cleaned_text)

        document.sections = sections.sections

        return document
