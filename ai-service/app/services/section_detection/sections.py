from pydantic import BaseModel, Field
from typing import List


class Section(BaseModel):
    title: str
    content: str
    lines: List[str] = Field(default_factory=list)


class DetectedSections(BaseModel):
    sections: List[Section] = Field(default_factory=list)
