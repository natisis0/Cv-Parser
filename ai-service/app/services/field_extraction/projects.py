import re
from app.models.document import Document
from app.models.project import Project
from .base import BaseFieldExtractor
from .projects_segmenter import ProjectsSegmenter
from app.services.field_extraction.skills_index import SkillsIndex

URL_PATTERN = r"https?://\S+"


class ProjectExtractor(BaseFieldExtractor):
    field_name = "projects"

    def __init__(self):
        self.segmenter = ProjectsSegmenter()
        self.skills_index = SkillsIndex()

    def extract(self, document: Document) -> None:
        section_text = document.get_section(self.field_name)
        if not section_text.strip():
            document.resume.projects = []
            return

        blocks = self.segmenter.segment(section_text)
        results = []

        for block in blocks:
            project_obj = self._parse_block(block)
            results.append(project_obj)

        document.resume.projects = results

    def _parse_block(self, block: str) -> Project:
        lines = block.split("\n")

        title = None
        description = []
        technologies = set()
        link = None

        for line in lines:
            clean = line.strip()
            if not clean:
                continue

            # URL detection
            if re.search(URL_PATTERN, clean):
                link = clean

            # Skills detection
            for variant, canonical in self.skills_index.lookup.items():
                if variant in clean.lower():
                    technologies.add(canonical)

            # Title guess
            if not title and len(clean.split()) <= 6:
                title = clean
            else:
                description.append(clean)

        if not title:
            title = "Unnamed Project"

        return Project(
            name=title,
            description=" ".join(description),
            technologies=list(technologies),
            link=link
        )
