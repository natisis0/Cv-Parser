from .base import PipelineStage
from app.services.preprocessing.enricher import SectionEnricher


class SectionEnrichmentStage(PipelineStage):

    def __init__(self):
        self.enricher = SectionEnricher()

    def process(self, document):

        for section in document.sections:
            self.enricher.enrich(section)

        return document
