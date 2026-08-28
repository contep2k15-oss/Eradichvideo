import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini")

    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
    ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")

    WHISPER_MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE", "distil-large-v3")
    WHISPER_DEVICE = os.getenv("WHISPER_DEVICE", "cuda")
    WHISPER_COMPUTE_TYPE = os.getenv("WHISPER_COMPUTE_TYPE", "int8")

    JOBS_DIR = os.getenv("JOBS_DIR", "./jobs")


settings = Settings()
os.makedirs(settings.JOBS_DIR, exist_ok=True)
