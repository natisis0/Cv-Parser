from pathlib import Path
from fastapi import HTTPException

from app.core.config import (
    ALLOWED_EXTENSIONS,
    MAX_FILE_SIZE,
)


def validate_file(filename: str, size: int):

    extension = Path(filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type."
        )

    if size > MAX_FILE_SIZE:
        max_size_mb = MAX_FILE_SIZE / (1024 * 1024)
        raise HTTPException(
            status_code=400,
            detail=f"File is too large. File must be smaller than {max_size_mb:g} MB."
        )