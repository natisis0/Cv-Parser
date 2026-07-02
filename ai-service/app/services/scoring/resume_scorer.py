class ResumeScorer:

    def score(self, resume) -> float:
        score = 0
        max_score = 7

        if resume.personal_info:
            if getattr(resume.personal_info, "email", None):
                score += 1
            if getattr(resume.personal_info, "full_name", None):
                score += 1

        if resume.experience:
            score += 1
        if resume.education:
            score += 1
        if resume.skills:
            score += 1
        if resume.projects:
            score += 1
        if resume.languages:
            score += 1

        return round(score / max_score, 2)
