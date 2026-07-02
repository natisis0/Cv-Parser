import re
from app.models.document import Document
from app.models.education import Education
from .base import BaseFieldExtractor
from .education_segmenter import EducationSegmenter, YEAR_PATTERN

DEGREE_KEYWORDS = [
    "bsc", "bachelor", "msc", "master",
    "phd", "diploma", "associate", "bs", "ms"
]

DATE_PATTERN = r"(19|20)\d{2}\s*[-–]\s*(19|20)\d{2}|Present"


class EducationExtractor(BaseFieldExtractor):
    field_name = "education"

    def __init__(self):
        self.segmenter = EducationSegmenter()

    def extract(self, document: Document) -> None:
        section_text = document.get_section(self.field_name)
        if not section_text.strip():
            document.resume.education = []
            return

        blocks = self.segmenter.segment(section_text)
        results = []

        for block in blocks:
            edu = self._parse_block(block)
            results.append(edu)

        document.resume.education = results

    def _parse_block(self, block: str) -> Education:
        lines = block.split("\n")

        institution = None
        degree = None
        field = None
        start_date = None
        end_date = None

        for line in lines:
            line_str = line.strip()
            if not line_str:
                continue

            low = line_str.lower()

            if any(k in low for k in DEGREE_KEYWORDS):
                degree = line_str

            if re.search(DATE_PATTERN, line_str):
                parts = re.split(r"[-–]", line_str)
                if len(parts) >= 2:
                    start_date = parts[0].strip()
                    end_date = parts[1].strip()
                else:
                    start_date = line_str

            if not institution and len(line_str.split()) > 1:
                institution = line_str

            if "computer" in low or "engineering" in low or "science" in low or "arts" in low or "business" in low or "mathematics" in low:
                field = line_str

        return Education(
            institution=institution,
            degree=degree,
            field=field,
            start_date=start_date,
            end_date=end_date
        )
