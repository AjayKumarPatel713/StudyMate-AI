
import os
from pathlib import Path

from dotenv import load_dotenv

# Project root directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from the project root .env file
load_dotenv(BASE_DIR / ".env")


class Settings:
    """Stores application configuration."""

    APP_NAME = "StudyMate AI"

    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

    # Can be changed through .env without modifying Python code
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")


settings = Settings()
