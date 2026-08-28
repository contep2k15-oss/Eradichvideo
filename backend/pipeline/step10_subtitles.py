"""
Bước 10: Sinh phụ đề .srt từ bản dịch cuối + timestamp gốc từ ASR.

Giới hạn số ký tự/dòng theo chuẩn đọc phổ biến (khoảng 42 ký tự/dòng, tối đa 2 dòng)
để phụ đề không bị tràn màn hình hoặc đọc không kịp.
"""
import os
import textwrap
from typing import List
from ..models import Segment

MAX_CHARS_PER_LINE = 42
MAX_LINES = 2


def _format_timestamp(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def _wrap_text(text: str) -> str:
    lines = textwrap.wrap(text, width=MAX_CHARS_PER_LINE)
    return "\n".join(lines[:MAX_LINES])


def build_srt(segments: List[Segment], out_dir: str, filename: str = "subtitles.srt") -> str:
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, filename)

    with open(out_path, "w", encoding="utf-8") as f:
        for idx, s in enumerate(segments, start=1):
            text = s.final_text
            if not text.strip():
                continue
            f.write(f"{idx}\n")
            f.write(f"{_format_timestamp(s.start)} --> {_format_timestamp(s.end)}\n")
            f.write(f"{_wrap_text(text)}\n\n")

    return out_path
