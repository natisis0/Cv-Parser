import re
from app.models.document import Document
from app.models.skill import Skill
from .base import BaseFieldExtractor
from app.services.field_extraction.skills_index import SkillsIndex


class SkillsExtractor(BaseFieldExtractor):
    field_name = "skills"

    def __init__(self):
        self.index = SkillsIndex()

    def extract(self, document: Document) -> None:
        # Query skills section if exists, fallback to cleaned_text
        section_text = document.get_section(self.field_name)
        text = (section_text if section_text.strip() else document.cleaned_text).lower()

        found = set()

        # STEP 1: direct matching
        words = re.split(r"[,\n/|]", text)
        for w in words:
            w = w.strip()
            norm = self.index.normalize(w)
            if norm:
                found.add(norm)

        # STEP 2: phrase scanning
        for variant, canonical in self.index.lookup.items():
            if variant in text:
                found.add(canonical)

        document.resume.skills = [Skill(name=norm) for norm in found]
