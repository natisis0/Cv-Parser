import re

YEAR_PATTERN = r"(19|20)\d{2}\s*[-–]\s*(19|20)\d{2}|Present"


class EducationSegmenter:

    def segment(self, text: str):
        lines = [l.strip() for l in text.splitlines() if l.strip()]

        blocks = []
        current = []

        for line in lines:
            is_boundary = (
                re.search(YEAR_PATTERN, line) or
                line.isupper() or
                len(line.split(",")) > 1
            )

            if is_boundary and current:
                blocks.append("\n".join(current))
                current = []

            current.append(line)

        if current:
            blocks.append("\n".join(current))

        return blocks
