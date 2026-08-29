"""
Bước 1: Input & nhận diện — tải video (nếu là link) hoặc dùng file đã upload.
Bước 2: Trích xuất audio để đưa vào ASR.

Chạy nhẹ, không cần GPU. yt-dlp và ffmpeg phải có sẵn trên máy (cài qua hệ điều hành).
"""
import os
import subprocess
from ..config import find_ffmpeg_binary


def download_video(url: str, out_dir: str) -> str:
    """Tải video từ link (YouTube/TikTok/Facebook...) bằng yt-dlp. Trả về đường dẫn file video."""
    import yt_dlp

    out_template = os.path.join(out_dir, "source.%(ext)s")
    ydl_opts = {
        "outtmpl": out_template,
        "format": "bestvideo[height<=1080]+bestaudio/best",
        "merge_output_format": "mp4",
        "quiet": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    for f in os.listdir(out_dir):
        if f.startswith("source."):
            return os.path.join(out_dir, f)
    raise RuntimeError("Tải video thất bại: không tìm thấy file output của yt-dlp")


def extract_audio(video_path: str, out_dir: str) -> str:
    """Tách audio mono 16kHz WAV — định dạng chuẩn faster-whisper khuyến nghị."""
    audio_path = os.path.join(out_dir, "audio.wav")
    cmd = [
        find_ffmpeg_binary("ffmpeg"), "-y", "-i", video_path,
        "-ac", "1", "-ar", "16000",
        "-vn", audio_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg tách audio lỗi: {result.stderr[-800:]}")
    return audio_path


def detect_genre(sample_text: str) -> str:
    """
    Nhận diện nhanh thể loại nội dung (hài / trang trọng / giáo dục / đời thường)
    từ một đoạn transcript mẫu, để các bước dịch sau điều chỉnh mức độ linh hoạt.
    Dùng LLM để phân loại thay vì rule cứng, cho linh hoạt hơn.
    """
    from ..llm_client import generate

    system = (
        "Bạn phân loại thể loại nội dung video dựa trên một đoạn transcript. "
        "Chỉ trả lời đúng 1 từ trong danh sách: hai, trang_trong, giao_duc, doi_thuong."
    )
    result = generate(system, sample_text[:2000]).strip().lower()
    allowed = {"hai", "trang_trong", "giao_duc", "doi_thuong"}
    return result if result in allowed else "doi_thuong"
