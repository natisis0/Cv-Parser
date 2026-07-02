class SectionEnricher:

    def enrich(self, section):

        section.lines = [
            line.strip()
            for line in section.content.splitlines()
            if line.strip()
        ]

        return section
