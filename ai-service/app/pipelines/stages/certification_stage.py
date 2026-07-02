from app.models.document import Document
from app.services.field_extraction.certifications import CertificationExtractor
from .base import PipelineStage


class CertificationStage(PipelineStage):

    def __init__(self):
        self.extractor = CertificationExtractor()

    def process(self, document: Document) -> Document:
        self.extractor.extract(document)
        return document
