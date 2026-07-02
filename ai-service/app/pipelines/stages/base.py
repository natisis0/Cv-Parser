from abc import ABC, abstractmethod

from app.models.document import Document


class PipelineStage(ABC):

    @abstractmethod
    def process(self, document: Document) -> Document:
        pass