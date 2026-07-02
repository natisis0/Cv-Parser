from abc import ABC, abstractmethod

from app.models.document import Document


class BaseFieldExtractor(ABC):
    field_name: str

    @abstractmethod
    def extract(self, document: Document) -> None:
        """
        Modifies the document in-place.
        """
        pass
