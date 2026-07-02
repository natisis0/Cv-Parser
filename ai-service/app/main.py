from fastapi import FastAPI

# from app.api.routes.health import router as health_router
from app.api.routes.resume import router as resume_router

app = FastAPI(title="CV Parser AI Service")

# app.include_router(health_router)
app.include_router(resume_router)