
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api.pyq_routes import router as pyq_router
from backend.config import settings
from backend.api.chat_routes import router as chat_router
from backend.api.document_routes import router as document_router
from backend.api.practice_routes import router as practice_router


app = FastAPI(
    title=settings.APP_NAME,
    description="AI-powered personalized learning assistant",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    return {
        "message": "Welcome to StudyMate AI",
        "status": "running"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "application": settings.APP_NAME
    }


app.include_router(chat_router)
app.include_router(document_router)
app.include_router(pyq_router)
app.include_router(practice_router)