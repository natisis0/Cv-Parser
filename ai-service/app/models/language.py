from pydantic import BaseModel
from typing import Optional


class Language(BaseModel):
    language: str
    level: Optional[str] = None
