import logging
import uuid
from pathlib import Path
from fastapi import UploadFile, HTTPException

from app.core.config import UPLOAD_DIR
from app.pipelines.resume_pipeline import ResumePipeline
from app.utils.file_utils import validate_file

# Import for parsing & cleaning
from app.services.parser import parse_resume
from app.services.preprocessing.cleaner import clean_text
from app.models.document import Document

# Import pipeline stages
from app.pipelines.stages.section_stage import SectionDetectionStage
from app.pipelines.stages.section_enrichment_stage import SectionEnrichmentStage
from app.pipelines.stages.header_stage import HeaderStage

# Import DI dependencies
from app.services.field_extraction.engine import ExtractionEngine
from app.services.field_extraction.personal_info import PersonalInfoExtractor
from app.services.field_extraction.skills import SkillsExtractor
from app.services.field_extraction.experience import ExperienceExtractor
from app.services.field_extraction.education import EducationExtractor
from app.services.field_extraction.projects import ProjectExtractor
from app.services.field_extraction.certifications import CertificationExtractor
from app.services.field_extraction.languages import LanguagesExtractor
from app.services.field_extraction.awards import AwardsExtractor

from app.services.validation.resume_validator import ResumeValidator
from app.services.resume_builder import ResumeBuilder
from app.services.scoring.resume_scorer import ResumeScorer

logger = logging.getLogger(__name__)

# 1. Instantiate the DI dependencies
engine = ExtractionEngine([
    PersonalInfoExtractor(),
    SkillsExtractor(),
    ExperienceExtractor(),
    EducationExtractor(),
    ProjectExtractor(),
    CertificationExtractor(),
    LanguagesExtractor(),
    AwardsExtractor()
])

validator = ResumeValidator()
builder = ResumeBuilder()
scorer = ResumeScorer()

run_pipeline = ResumePipeline(engine, validator, builder, scorer)


class ResumeService:

    def __init__(self):
        # Instantiate stages
        self.section_detection = SectionDetectionStage()
        self.section_enrichment = SectionEnrichmentStage()
        self.header_extraction = HeaderStage()

    async def parse(self, file: UploadFile) -> dict:
        # Read file bytes in memory
        content = await file.read()

        # Validate extension and size before writing to disk
        validate_file(file.filename, len(content))

        # Generate a unique UUID filename to avoid overwrites
        extension = Path(file.filename).suffix.lower()
        unique_filename = f"{uuid.uuid4()}{extension}"
        file_path = UPLOAD_DIR / unique_filename

        try:
            # Save file to disk
            with open(file_path, "wb") as buffer:
                buffer.write(content)

            # 1. Parse raw text and clean it
            raw_text = parse_resume(str(file_path))
            cleaned_text = clean_text(raw_text)

            # 2. Create Document model
            document = Document(raw_text=raw_text, cleaned_text=cleaned_text)

            # 3. Process structure & enrichment stages
            document = self.section_detection.process(document)
            document = self.section_enrichment.process(document)
            document = self.header_extraction.process(document)

            # 4. Run the final resume parsing pipeline
            pipeline_result = run_pipeline.run(document)

            # Return structured success response
            return {
                "success": True,
                "filename": file.filename,
                "data": pipeline_result
            }
        except HTTPException:
            # Propagate FastAPI HTTPExceptions directly
            raise
        except Exception as e:
            # Log the full exception internally
            logger.exception(f"Error parsing resume {file.filename}: {e}")
            # Raise a clean, generic HTTPException without leaking implementation details
            raise HTTPException(
                status_code=500,
                detail="Failed to parse resume."
            )
        finally:
            # Ensure temporary file is always cleaned up
            if file_path.exists():
                try:
                    file_path.unlink()
                except Exception:
                    pass



