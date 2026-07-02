from app.models.document import Document
from app.services.field_extraction.personal_info import PersonalInfoExtractor
from .base import PipelineStage


class PersonalInfoStage(PipelineStage):

    def __init__(self):
        self.extractor = PersonalInfoExtractor()

    def process(self, document: Document) -> Document:

        self.extractor.extract(document)

        return document
