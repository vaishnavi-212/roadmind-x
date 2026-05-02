from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.routes.detect_route import router
from app.db.session import engine
from app.db.models import Base

# Create tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.APP_NAME,
    description="AI-powered spatial memory system for road hazard detection",
    version="1.0.0",
    debug=settings.DEBUG
)

# CORS — allow all origins for now (tighten later)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(router)

@app.get("/")
def root():
    return {
        "app": settings.APP_NAME,
        "status": "running",
        "version": "1.0.0"
    }

@app.get("/health")
def health():
    return {"status": "ok"}