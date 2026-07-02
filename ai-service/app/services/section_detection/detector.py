from app.services.section_detection.sections import Section, DetectedSections
from .keywords import SECTION_KEYWORDS
from .utils import normalize


def detect_sections(text: str) -> DetectedSections:

    lines = text.split("\n")

    sections = []
    current_section = None
    current_content = []

    for i, line in enumerate(lines):
        cleaned = normalize(line)

        matched_section = None

        for section_name, keywords in SECTION_KEYWORDS.items():
            if cleaned in keywords:
                matched_section = section_name
                break

        if matched_section:

            # save previous section
            if current_section:
                sections.append(
                    Section(
                        title=current_section,
                        content="\n".join(current_content),
                        lines=current_content
                    )
                )

            current_section = matched_section
            current_content = []

        else:
            current_content.append(line)

    # last section
    if current_section:
        sections.append(
            Section(
                title=current_section,
                content="\n".join(current_content),
                lines=current_content
            )
        )

    return DetectedSections(sections=sections)
