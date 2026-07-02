from app.models.document import Document
from app.services.field_extraction.languages import LanguagesExtractor
from .base import PipelineStage


class LanguagesStage(PipelineStage):

    def __init__(self):
        self.extractor = LanguagesExtractor()

    def process(self, document: Document) -> Document:
        self.extractor.extract(document)
        return document
