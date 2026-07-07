import uuid
import logging
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException

from app.core.config import UPLOAD_DIR
from app.utils.file_utils import validate_file
from app.services.resume_service import ResumeService
from app.services.spacy_parser_demo_check import parse_with_spacy

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/resume", tags=["Resume"])
resume_service = ResumeService()


@router.post("/parse")
async def parse_resume(file: UploadFile = File(...)):
    return await resume_service.parse(file)


@router.post("/parse-spacy")
async def parse_resume_spacy(file: UploadFile = File(...)):
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

        # Parse using the new spaCy model
        entities = parse_with_spacy(str(file_path))

        return {
            "success": True,
            "filename": file.filename,
            "entities": entities
        }
    except Exception as e:
        logger.exception(f"Error parsing resume via spaCy {file.filename}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse resume via spaCy: {str(e)}"
        )
    finally:
        # Ensure temporary file is always cleaned up
        if file_path.exists():
            try:
                file_path.unlink()
            except Exception:
                pass
