from pydantic import BaseModel, Field
from app.models.resume import Resume


class Document(BaseModel):
    raw_text: str
    cleaned_text: str
    sections: list = []
    header: str = ""
    resume: Resume = Field(default_factory=Resume)

    def get_section(self, section_title: str) -> str:
        for section in self.sections:
            title = getattr(section, "title", None)
            if title and title.lower() == section_title.lower():
                return getattr(section, "content", "")
        return ""