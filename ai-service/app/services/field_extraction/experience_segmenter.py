import re

DATE_RANGE_REGEX = r"(\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}|\b\d{4})\s*(?:-|–|—|to)\s*(Present|\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}|\b\d{4})"


class ExperienceSegmenter:

    def segment(self, section_text: str) -> list[str]:
        if not section_text.strip():
            return []

        lines = section_text.splitlines()
        n = len(lines)

        # Find indices of lines that contain date ranges
        date_indices = []
        for i, line in enumerate(lines):
            if re.search(DATE_RANGE_REGEX, line, re.IGNORECASE):
                date_indices.append(i)

        if not date_indices:
            # Fallback: if no date ranges are found, return the whole text as a single entry
            return [section_text]

        # Determine boundaries of each job entry
        starts = []
        for idx in date_indices:
            start_candidate = idx
            for offset in [1, 2]:
                prev_idx = idx - offset
                if prev_idx >= 0:
                    # Don't go past the previous date range
                    if date_indices and prev_idx <= date_indices[date_indices.index(idx) - 1]:
                        break
                    # If the line is short, it's likely company/title
                    if len(lines[prev_idx].strip().split()) <= 6:
                        start_candidate = prev_idx
            starts.append(start_candidate)

        # Now slice the lines into entries based on the starts list
        entries = []
        for i in range(len(starts)):
            start_idx = starts[i]
            end_idx = starts[i + 1] if i + 1 < len(starts) else n
            entry_lines = lines[start_idx:end_idx]
            entry_text = "\n".join(entry_lines).strip()
            if entry_text:
                entries.append(entry_text)

        return entries
