from app.models.document import Document
from app.services.field_extraction.awards import AwardsExtractor
from .base import PipelineStage


class AwardsStage(PipelineStage):

    def __init__(self):
        self.extractor = AwardsExtractor()

    def process(self, document: Document) -> Document:
        self.extractor.extract(document)
        return document
