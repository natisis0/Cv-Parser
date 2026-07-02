from fastapi import APIRouter, UploadFile, File

from app.services.resume_service import ResumeService

router = APIRouter(prefix="/resume", tags=["Resume"])
resume_service = ResumeService()


@router.post("/parse")
async def parse_resume(file: UploadFile = File(...)):
    return await resume_service.parse(file)