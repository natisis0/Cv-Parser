from data.knowledge.skills_base import SKILLS


class SkillsIndex:

    def __init__(self):

        self.lookup = {}

        for canonical, variants in SKILLS.items():
            for v in variants:
                self.lookup[v.lower()] = canonical

    def normalize(self, skill: str):

        return self.lookup.get(skill.lower())
