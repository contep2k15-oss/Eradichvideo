"""
Bước 12: Xuất theo định dạng nền tảng — KHÔNG tự động đăng.

Xuất nhiều bản từ video cuối, mỗi bản đúng tỷ lệ/spec khuyến nghị của từng nền
tảng, lưu vào thư mục output/<nen_tang>/ để người dùng tự tải lên tay.
"""
import os
import subprocess
from typing import Dict

# preset: (width, height, video_bitrate)
PRESETS = {
    "youtube_16_9": (1920, 1080, "8M"),
    "youtube_shorts_9_16": (1080, 1920, "6M"),
    "tiktok_9_16": (1080, 1920, "6M"),
    "facebook_reels_9_16": (1080, 1920, "6M"),
    "instagram_1_1": (1080, 1080, "6M"),
}


def _crop_scale_filter(target_w: int, target_h: int) -> str:
    """Crop-to-fill rồi scale đúng kích thước đích, giữ phần giữa khung hình (an toàn cho hầu hết nội dung)."""
    return (
        f"scale={target_w}:{target_h}:force_original_aspect_ratio=increase,"
        f"crop={target_w}:{target_h}"
    )


def export_all(final_video_path: str, out_dir: str, use_nvenc: bool = True) -> Dict[str, str]:
    os.makedirs(out_dir, exist_ok=True)
    results = {}

    for name, (w, h, bitrate) in PRESETS.items():
        platform_dir = os.path.join(out_dir, name)
        os.makedirs(platform_dir, exist_ok=True)
        out_path = os.path.join(platform_dir, f"{name}.mp4")

        video_codec = ["-c:v", "h264_nvenc"] if use_nvenc else ["-c:v", "libx264"]
        cmd = [
            "ffmpeg", "-y", "-i", final_video_path,
            "-vf", _crop_scale_filter(w, h),
            *video_codec, "-b:v", bitrate,
            "-c:a", "aac", "-b:a", "128k",
            out_path,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0 and use_nvenc:
            cmd[cmd.index("h264_nvenc")] = "libx264"
            result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            results[name] = out_path
        # nếu 1 preset lỗi, không làm sập toàn bộ export — bỏ qua preset đó và tiếp tục

    return results
