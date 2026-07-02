from app.models.document import Document
from app.services.field_extraction.skills import SkillsExtractor
from .base import PipelineStage


class SkillsStage(PipelineStage):

    def __init__(self):
        self.extractor = SkillsExtractor()

    def process(self, document: Document) -> Document:
        self.extractor.extract(document)
        return document
