from pydantic import BaseModel
from typing import List, Optional, Any


class FieldConfidence(BaseModel):
    value: Any
    confidence: float


class NormalizedResume(BaseModel):
    personal_info: dict
    skills: List[str]
    education: List[dict]
    experience: List[dict]
    projects: List[dict]
    certifications: List[str]
    languages: List[dict]
    awards: List[str]

    completeness_score: float
