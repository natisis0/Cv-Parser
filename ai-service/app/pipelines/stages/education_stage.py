from app.models.document import Document
from app.services.field_extraction.education import EducationExtractor
from .base import PipelineStage


class EducationStage(PipelineStage):

    def __init__(self):
        self.extractor = EducationExtractor()

    def process(self, document: Document) -> Document:
        self.extractor.extract(document)
        return document
