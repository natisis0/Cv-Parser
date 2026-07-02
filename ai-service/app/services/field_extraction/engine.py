import logging

logger = logging.getLogger(__name__)


class ExtractionEngine:

    def __init__(self, extractors: list):
        self.extractors = extractors

    def run(self, document):
        for extractor in self.extractors:
            logger.info(f"Running {extractor.__class__.__name__} for field: '{extractor.field_name}'...")
            extractor.extract(document)

        return document
