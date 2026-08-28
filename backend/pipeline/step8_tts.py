"""
Bước 8: Tạo giọng lồng tiếng (TTS đa ngôn ngữ).

Mặc định dùng Edge-TTS: free, cloud (không tốn VRAM máy bạn), hỗ trợ rất nhiều
ngôn ngữ/giọng — lựa chọn tối ưu chi phí nhất theo đúng thiết kế pipeline.

Sinh audio RIÊNG cho từng segment (theo final_text của Segment), rồi bước 9
sẽ co giãn từng đoạn cho khớp khung thời gian gốc trước khi bước 11 ghép lại.
"""
import os
from typing import List
from ..models import Segment

# Map một số ngôn ngữ phổ biến sang giọng mặc định của Edge-TTS.
# Có thể mở rộng/tùy biến theo nhu cầu (giọng nam/nữ, vùng miền).
DEFAULT_VOICES = {
    "vi": "vi-VN-HoaiMyNeural",
    "en": "en-US-AriaNeural",
    "ja": "ja-JP-NanamiNeural",
    "ko": "ko-KR-SunHiNeural",
    "zh": "zh-CN-XiaoxiaoNeural",
    "th": "th-TH-PremwadeeNeural",
    "id": "id-ID-GadisNeural",
    "es": "es-ES-ElviraNeural",
    "fr": "fr-FR-DeniseNeural",
}


async def synthesize_segments(segments: List[Segment], target_lang: str, out_dir: str) -> List[str]:
    """Trả về danh sách đường dẫn file audio (1 file/segment, theo đúng thứ tự segments)."""
    import edge_tts

    voice = DEFAULT_VOICES.get(target_lang, "en-US-AriaNeural")
    os.makedirs(out_dir, exist_ok=True)

    paths = []
    for s in segments:
        text = s.final_text
        out_path = os.path.join(out_dir, f"seg_{s.id:04d}.mp3")
        if text.strip():
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(out_path)
        else:
            # segment rỗng (VD: khoảng lặng) — bỏ qua, không tạo file
            out_path = None
        paths.append(out_path)
    return paths
