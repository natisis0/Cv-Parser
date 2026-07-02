from pydantic import BaseModel
from typing import List, Optional


class Project(BaseModel):
    name: str
    description: str
    technologies: List[str] = []
    link: Optional[str] = None
