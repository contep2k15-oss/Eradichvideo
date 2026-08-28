import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # "gemini" (SDK Google chính chủ) | "anthropic" (SDK Anthropic chính chủ)
    # | "openai_compatible" (proxy/reseller kiểu shopaikey.com, gọi qua REST chuẩn OpenAI)
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini")

    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
    ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")

    # Provider dạng OpenAI-compatible (proxy bên thứ 3) — điền BASE_URL chính xác
    # theo tài liệu của nhà cung cấp, ví dụ: https://shopaikey.com/v1
    OPENAI_COMPAT_API_KEY = os.getenv("OPENAI_COMPAT_API_KEY", "")
    OPENAI_COMPAT_BASE_URL = os.getenv("OPENAI_COMPAT_BASE_URL", "")
    OPENAI_COMPAT_MODEL = os.getenv("OPENAI_COMPAT_MODEL", "gemini-3.7-flash")

    WHISPER_MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE", "distil-large-v3")
    WHISPER_DEVICE = os.getenv("WHISPER_DEVICE", "cuda")
    WHISPER_COMPUTE_TYPE = os.getenv("WHISPER_COMPUTE_TYPE", "int8")

    JOBS_DIR = os.getenv("JOBS_DIR", "./jobs")


settings = Settings()
os.makedirs(settings.JOBS_DIR, exist_ok=True)
