import re

BULLET_PATTERN = r"^[•\-*]\s+"


class ProjectsSegmenter:

    def segment(self, text: str):
        lines = [l.strip() for l in text.splitlines() if l.strip()]

        projects = []
        current = []

        for line in lines:
            is_new_project = (
                re.match(BULLET_PATTERN, line) or
                line.isupper() or
                len(line.split()) <= 6 and line[0].isalpha()
            )

            if is_new_project and current:
                projects.append("\n".join(current))
                current = []

            current.append(line)

        if current:
            projects.append("\n".join(current))

        return projects
