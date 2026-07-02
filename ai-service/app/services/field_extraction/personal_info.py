import re

EMAIL_REGEX = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
PHONE_REGEX = r"(\+?\d[\d\s\-]{7,}\d)"
LINKEDIN_REGEX = r"(https?://)?(www\.)?linkedin\.com/in/[a-zA-Z0-9\-_%]+"
GITHUB_REGEX = r"(https?://)?(www\.)?github\.com/[a-zA-Z0-9\-_%]+"


from app.models.document import Document
from app.models.personal_info import PersonalInfo
from .base import BaseFieldExtractor


class PersonalInfoExtractor(BaseFieldExtractor):
    field_name = "personal_info"

    def extract(self, document: Document) -> None:
        text = document.header

        email = self._extract_email(text)
        phone = self._extract_phone(text)
        linkedin = self._extract_linkedin(text)
        github = self._extract_github(text)
        name = self._extract_name(text)
        location = self._extract_location(text)

        document.resume.personal_info = PersonalInfo(
            full_name=name,
            email=email,
            phone=phone,
            linkedin=linkedin,
            github=github,
            location=location
        )

    def _extract_email(self, text):
        match = re.search(EMAIL_REGEX, text)
        return match.group() if match else None

    def _extract_phone(self, text):
        match = re.search(PHONE_REGEX, text)
        return match.group() if match else None

    def _extract_linkedin(self, text):
        match = re.search(LINKEDIN_REGEX, text)
        return match.group() if match else None

    def _extract_github(self, text):
        match = re.search(GITHUB_REGEX, text)
        return match.group() if match else None

    def _extract_name(self, text):
        lines = text.split("\n")

        for line in lines[:5]:
            line = line.strip()

            if len(line.split()) <= 4 and line.istitle():
                return line

        return None

    def _extract_location(self, text):
        match = re.search(r"([A-Z][a-zA-Z\s]{1,30}),\s*([A-Z][a-zA-Z\s]{1,30})", text)
        return match.group() if match else None
