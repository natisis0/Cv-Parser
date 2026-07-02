from pydantic import BaseModel
from typing import Optional


class Certification(BaseModel):
    name: str
    issuer: Optional[str] = None
    date: Optional[str] = None
