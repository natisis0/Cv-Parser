from app.models.document import Document
from app.services.preprocessing.cleaner import clean_text

from .base import PipelineStage


class CleaningStage(PipelineStage):

    def process(self, document: Document) -> Document:

        document.cleaned_text = clean_text(document.raw_text)

        return document