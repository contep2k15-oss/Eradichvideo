"""
Bước 11: Ghép audio lồng tiếng (đã đồng bộ ở bước 9) + phụ đề vào video gốc.

Dùng ffmpeg + NVENC (h264_nvenc) để encode nhanh bằng encoder riêng của GPU,
không đụng vào VRAM đang dùng cho các model AI (ASR/LLM/TTS local) — cho phép
bước này chạy độc lập, không phải chờ giải phóng VRAM AI.

Quy trình:
1. Ghép các file audio segment đã sync thành 1 track audio liên tục (chèn khoảng lặng đúng vị trí).
2. Mux track audio đó + phụ đề (soft-sub, không burn cứng) vào video gốc.
"""
import os
import subprocess
from typing import List, Optional
from ..models import Segment
from ..config import find_ffmpeg_binary


def build_full_audio_track(
    segment_audio_paths: List[Optional[str]],
    segments: List[Segment],
    total_duration: float,
    out_dir: str,
) -> str:
    """Dùng ffmpeg filter_complex để đặt từng segment audio đúng vị trí start-time trên 1 track dài = total_duration."""
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "dubbed_track.wav")

    valid = [(p, s) for p, s in zip(segment_audio_paths, segments) if p and os.path.exists(p)]
    if not valid:
        raise RuntimeError("Không có audio segment nào hợp lệ để ghép track lồng tiếng")

    inputs = []
    filter_parts = []
    for i, (path, seg) in enumerate(valid):
        inputs += ["-i", path]
        delay_ms = int(seg.start * 1000)
        filter_parts.append(f"[{i}:a]adelay={delay_ms}|{delay_ms}[a{i}]")

    mix_inputs = "".join(f"[a{i}]" for i in range(len(valid)))
    filter_complex = ";".join(filter_parts) + f";{mix_inputs}amix=inputs={len(valid)}:normalize=0[out]"

    cmd = [
        find_ffmpeg_binary("ffmpeg"), "-y", *inputs,
        "-filter_complex", filter_complex,
        "-map", "[out]",
        "-t", str(total_duration),
        out_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg ghép track audio lỗi: {result.stderr[-800:]}")
    return out_path


def mux_final_video(
    video_path: str,
    dubbed_audio_path: str,
    subtitle_path: Optional[str],
    out_dir: str,
    use_nvenc: bool = True,
) -> str:
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "final.mp4")

    video_codec = ["-c:v", "h264_nvenc"] if use_nvenc else ["-c:v", "libx264"]

    cmd = [find_ffmpeg_binary("ffmpeg"), "-y", "-i", video_path, "-i", dubbed_audio_path]
    if subtitle_path and os.path.exists(subtitle_path):
        cmd += ["-i", subtitle_path]
        cmd += ["-map", "0:v:0", "-map", "1:a:0", "-map", "2:0"]
        cmd += ["-c:s", "mov_text"]  # soft-sub, người xem tự bật/tắt được
    else:
        cmd += ["-map", "0:v:0", "-map", "1:a:0"]

    cmd += video_codec + ["-c:a", "aac", "-shortest", out_path]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0 and use_nvenc:
        # fallback về CPU encode nếu máy không có NVENC khả dụng lúc runtime
        return mux_final_video(video_path, dubbed_audio_path, subtitle_path, out_dir, use_nvenc=False)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg mux video cuối lỗi: {result.stderr[-800:]}")
    return out_path
