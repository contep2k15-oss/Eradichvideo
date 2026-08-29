import os
import sys
from dotenv import load_dotenv

load_dotenv()


def resource_path(*parts) -> str:
    """
    Trả về đường dẫn đúng dù app đang chạy dạng mã nguồn thường (python -m ...)
    hay đã được PyInstaller đóng gói thành 1 file .exe (lúc đó file được giải nén
    tạm vào thư mục sys._MEIPASS, không phải thư mục chứa file .py nữa).
    """
    if getattr(sys, "frozen", False):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, *parts)


def find_ffmpeg_binary(binary_name: str) -> str:
    """
    Tìm ffmpeg/ffprobe theo thứ tự ưu tiên:
    1. Bản nhúng sẵn cùng thư mục với file .exe khi đã đóng gói (giống cách
       ai-era-media-2 nhúng ffmpeg-static — người dùng không cần tự cài ffmpeg).
    2. Nếu không có bản nhúng, dùng lệnh hệ thống bình thường (yêu cầu đã cài
       ffmpeg và có trong PATH — đúng như khi chạy bằng mã nguồn thông thường).
    """
    exe_name = f"{binary_name}.exe" if os.name == "nt" else binary_name

    if getattr(sys, "frozen", False):
        bundled = os.path.join(os.path.dirname(sys.executable), "ffmpeg_bin", exe_name)
        if os.path.exists(bundled):
            return bundled

    return binary_name  # fallback: trông cậy vào PATH hệ thống


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
