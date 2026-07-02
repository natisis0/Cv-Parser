from app.services.parser import parse_resume
from app.services.preprocessing.cleaner import clean_text


class ResumePipeline:

    def __init__(self, engine, validator, builder, scorer):
        self.engine = engine
        self.validator = validator
        self.builder = builder
        self.scorer = scorer

    def run(self, document):
        # 1. Run extraction engine
        document = self.engine.run(document)

        # 2. Build final resume
        resume = self.builder.build(document)

        # 3. Validate
        validation = self.validator.validate(resume)

        # 4. Score
        score = self.scorer.score(resume)

        return {
            "resume": resume,
            "validation": validation,
            "metadata": {
                "completeness_score": score
            }
        }