"""
Bước 9: Đồng bộ thời lượng (time-stretch).

Câu dịch thường dài/ngắn hơn câu gốc khi đọc thành tiếng. Dùng ffmpeg atempo
để co giãn TỐC ĐỘ audio (không đổi cao độ giọng) cho mỗi segment khớp với
khung thời gian [start, end] gốc lấy từ ASR, tránh lệch nhịp khi ghép vào video.

Giới hạn atempo trong khoảng an toàn để giọng không bị méo quá mức
(atempo hỗ trợ 0.5–2.0 mỗi lần gọi, cần chain nhiều lần nếu vượt khoảng này).
"""
import os
import subprocess
from typing import List, Optional
from ..models import Segment

MIN_ATEMPO, MAX_ATEMPO = 0.85, 1.35  # giới hạn co giãn để giọng không bị biến dạng nghe rõ


def _get_duration(path: str) -> float:
    cmd = [
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return float(result.stdout.strip() or 0)


def sync_segment_audio(segment_audio_path: Optional[str], segment: Segment, out_dir: str) -> Optional[str]:
    if not segment_audio_path or not os.path.exists(segment_audio_path):
        return None

    target_duration = max(segment.end - segment.start, 0.1)
    actual_duration = _get_duration(segment_audio_path)
    if actual_duration <= 0:
        return segment_audio_path

    tempo = actual_duration / target_duration
    tempo = max(MIN_ATEMPO, min(MAX_ATEMPO, tempo))

    out_path = os.path.join(out_dir, os.path.basename(segment_audio_path).replace(".mp3", "_synced.mp3"))
    cmd = [
        "ffmpeg", "-y", "-i", segment_audio_path,
        "-filter:a", f"atempo={tempo:.3f}",
        out_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        # nếu lỗi, trả về file gốc chưa co giãn thay vì làm sập cả pipeline
        return segment_audio_path
    return out_path


def sync_all(segment_audio_paths: List[Optional[str]], segments: List[Segment], out_dir: str) -> List[Optional[str]]:
    os.makedirs(out_dir, exist_ok=True)
    return [
        sync_segment_audio(path, seg, out_dir)
        for path, seg in zip(segment_audio_paths, segments)
    ]
