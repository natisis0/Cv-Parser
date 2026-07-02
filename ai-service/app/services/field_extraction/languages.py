import re
from app.models.document import Document
from app.models.language import Language
from .base import BaseFieldExtractor


class LanguagesExtractor(BaseFieldExtractor):
    field_name = "languages"

    def extract(self, document: Document) -> None:
        section_text = document.get_section(self.field_name)
        if not section_text.strip():
            document.resume.languages = []
            return

        languages = []
        for line in section_text.splitlines():
            clean_line = line.strip()
            if not clean_line:
                continue

            if "-" in clean_line or ":" in clean_line:
                parts = re.split(r"[-:]", clean_line)
                if len(parts) >= 2:
                    languages.append(
                        Language(
                            language=parts[0].strip(),
                            level=parts[1].strip()
                        )
                    )
            else:
                languages.append(
                    Language(
                        language=clean_line,
                        level=None
                    )
                )

        document.resume.languages = languages
