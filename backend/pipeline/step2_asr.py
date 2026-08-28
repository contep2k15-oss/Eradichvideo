"""
Bước 2: Trích xuất transcript có timestamp bằng faster-whisper.

Chạy LOCAL trên GPU của bạn. Với GPU 6GB (GTX 1660 Ti/Super):
- WHISPER_MODEL_SIZE nên để "distil-large-v3" hoặc "medium" trong .env
- WHISPER_COMPUTE_TYPE nên để "int8" để tiết kiệm VRAM

Model được load rồi giải phóng ngay sau khi dùng xong (không giữ trong RAM/VRAM
giữa các job) để nhường chỗ cho bước LLM/TTS chạy sau, đúng nguyên tắc
"1 model AI tại 1 thời điểm" đã thống nhất trong thiết kế pipeline.
"""
from typing import List
from ..config import settings
from ..models import Segment


def transcribe(audio_path: str) -> List[Segment]:
    from faster_whisper import WhisperModel

    model = WhisperModel(
        settings.WHISPER_MODEL_SIZE,
        device=settings.WHISPER_DEVICE,
        compute_type=settings.WHISPER_COMPUTE_TYPE,
    )
    try:
        segments_iter, info = model.transcribe(audio_path, vad_filter=True)
        segments: List[Segment] = []
        for i, seg in enumerate(segments_iter):
            segments.append(
                Segment(
                    id=i,
                    start=seg.start,
                    end=seg.end,
                    source_text=seg.text.strip(),
                )
            )
        return segments
    finally:
        # Giải phóng VRAM ngay — quan trọng với GPU 6GB vì bước LLM local (nếu có)
        # hoặc TTS local (XTTS) chạy tiếp theo cần VRAM trống.
        del model
