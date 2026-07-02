from app.models.document import Document
from app.services.field_extraction.projects import ProjectExtractor
from .base import PipelineStage


class ProjectsStage(PipelineStage):

    def __init__(self):
        self.extractor = ProjectExtractor()

    def process(self, document: Document) -> Document:
        self.extractor.extract(document)
        return document
