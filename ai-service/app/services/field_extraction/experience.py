import re
from typing import Tuple, Optional
from app.models.document import Document
from app.models.experience import Experience
from .base import BaseFieldExtractor
from .experience_segmenter import ExperienceSegmenter, DATE_RANGE_REGEX

COMMON_TECH = {"python", "javascript", "typescript", "java", "c++", "c#", "ruby", "go", "rust", "php", "html", "css", "react", "angular", "vue", "node", "django", "flask", "fastapi", "spring", "docker", "kubernetes", "aws", "azure", "gcp", "sql", "postgres", "mysql", "mongodb", "redis", "git", "linux", "terraform"}

TECH_MAP = {
    "python": "Python", "javascript": "JavaScript", "typescript": "TypeScript",
    "java": "Java", "c++": "C++", "c#": "C#", "ruby": "Ruby", "go": "Go",
    "rust": "Rust", "php": "PHP", "html": "HTML", "css": "CSS", "react": "React",
    "angular": "Angular", "vue": "Vue", "node": "Node.js", "django": "Django",
    "flask": "Flask", "fastapi": "FastAPI", "spring": "Spring Boot",
    "docker": "Docker", "kubernetes": "Kubernetes", "aws": "AWS", "azure": "Azure",
    "gcp": "GCP", "sql": "SQL", "postgres": "PostgreSQL", "mysql": "MySQL",
    "mongodb": "MongoDB", "redis": "Redis", "git": "Git", "linux": "Linux",
    "terraform": "Terraform"
}


class ExperienceExtractor(BaseFieldExtractor):
    field_name = "experience"

    def __init__(self):
        self.segmenter = ExperienceSegmenter()

    def extract(self, document: Document) -> None:
        section_text = document.get_section(self.field_name)
        if not section_text.strip():
            document.resume.experience = []
            return

        entries = self.segmenter.segment(section_text)
        experiences = []

        for entry in entries:
            exp = self._parse_entry(entry)
            experiences.append(exp)

        document.resume.experience = experiences

    def _parse_entry(self, entry_text: str) -> Experience:
        lines = entry_text.splitlines()
        
        # 1. Date Range Extraction
        start_date = None
        end_date = None
        date_line_idx = -1
        
        for idx, line in enumerate(lines):
            match = re.search(DATE_RANGE_REGEX, line, re.IGNORECASE)
            if match:
                start_date = match.group(1).strip()
                end_date = match.group(2).strip()
                date_line_idx = idx
                break

        # 2. Company & Title Extraction
        company = None
        title = None
        
        # If date line is found, everything before it is title/company
        if date_line_idx != -1:
            pre_date_lines = lines[:date_line_idx]
            company, title = self._extract_company_and_title(pre_date_lines)
            post_date_lines = lines[date_line_idx + 1:]
        else:
            # Fallback: first line company, second title, rest description
            if len(lines) >= 1:
                company = lines[0].strip()
            if len(lines) >= 2:
                title = lines[1].strip()
            post_date_lines = lines[2:]

        # 3. Description Extraction
        description = "\n".join(post_date_lines).strip()

        # 4. Technologies Extraction
        words = set(re.findall(r"\b[a-zA-Z0-9+#.-]+\b", entry_text.lower()))
        techs = [TECH_MAP[t] for t in COMMON_TECH if t in words and t in TECH_MAP]

        return Experience(
            company=company,
            title=title,
            start_date=start_date,
            end_date=end_date,
            description=description,
            technologies=techs
        )

    def _extract_company_and_title(self, pre_date_lines: list[str]) -> Tuple[Optional[str], Optional[str]]:
        clean_lines = [line.strip() for line in pre_date_lines if line.strip()]
        if not clean_lines:
            return None, None
        
        if len(clean_lines) == 1:
            line = clean_lines[0]
            title_keywords = {"engineer", "developer", "manager", "analyst", "lead", "consultant", "director", "architect", "intern", "specialist", "officer", "programmer"}
            if any(word in line.lower() for word in title_keywords):
                return None, line
            return line, None
            
        # Default to first line as company, second line as title
        line1 = clean_lines[0]
        line2 = clean_lines[1]
        return line1, line2
