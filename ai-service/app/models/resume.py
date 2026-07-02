from pydantic import BaseModel
from typing import List, Optional

from .personal_info import PersonalInfo
from .education import Education
from .experience import Experience
from .project import Project
from .certification import Certification
from .skill import Skill
from .language import Language


class Resume(BaseModel):
    personal_info: Optional[PersonalInfo] = None
    skills: List[Skill] = []
    education: List[Education] = []
    experience: List[Experience] = []
    projects: List[Project] = []
    certifications: List[Certification] = []
    languages: List[Language] = []
    awards: List[str] = []