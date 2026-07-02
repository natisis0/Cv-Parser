# AI Service - CV Parser

The AI and text processing backend service for parsing and extracting metadata from resumes / CVs.

## Features

- **CV Text Extraction**: Supports plain text, PDF parsing, and DOCX files.
- **NLP Information Extraction**: Automatically identifies personal details (name, email, phone), skills, education history, and work experience.
- **Pipeline Architecture**: Structured parsing stages: `cleaner` -> `parser` -> `extractor`.
- **API Service**: Exposes FastAPI endpoints for base64 or file upload requests.

## Project Structure

```text
app/
├── api/            # API endpoints & routing
├── core/           # Configuration and logger setup
├── models/         # Pydantic schema validation models
├── pipelines/      # ML/NLP processing pipelines
├── services/       # Core business logic services (cleaner, parser, extractor)
└── utils/          # Auxiliary file utilities
```

## Running the Service Locally

This project uses [uv](https://github.com/astral-sh/uv) for dependency management.

1. Install `uv` if not already available:
   ```bash
   pip install uv
   ```

2. Synchronize dependencies:
   ```bash
   uv sync
   ```

3. Run the FastAPI development server:
   ```bash
   uv run uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
   ```

The API docs will be available at [http://localhost:8001/docs](http://localhost:8001/docs).
