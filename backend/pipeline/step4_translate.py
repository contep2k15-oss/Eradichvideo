"""
Bước 4: Dịch nghĩa (pass 1 — "sát nghĩa").

Nguyên tắc quan trọng: KHÔNG dịch từng câu rời rạc. Đưa cả cụm segment liền kề
làm context cho LLM để giữ mạch văn xuyên suốt, vì dịch từng câu độc lập
(kiểu MT truyền thống) thường làm mất mạch ý, đặc biệt với hội thoại nhiều lượt.

Với các segment đã bị đánh dấu is_culture_sensitive=True ở bước 3, bản dịch ở
bước này chỉ là bản nháp tham khảo nghĩa gốc — bước 5 mới quyết định bản cuối.
"""
from typing import List
from ..models import Segment
from ..llm_client import generate_json

BATCH_SIZE = 20

SYSTEM_PROMPT_TMPL = """Bạn là dịch giả chuyên nghiệp, dịch transcript video từ
tiếng {source_lang} sang tiếng {target_lang}.

Yêu cầu:
- Dịch SÁT NGHĨA, giữ đúng ý gốc, không thêm/bớt thông tin.
- Đọc toàn bộ đoạn transcript được cung cấp để hiểu mạch truyện trước khi dịch,
  không dịch từng câu như thể nó đứng độc lập.
- Giữ văn phong phù hợp thể loại nội dung: {genre}.
- Với câu đã được đánh dấu [NHAY_VAN_HOA], vẫn dịch sát nghĩa đen bình thường ở bước
  này — sẽ có bước riêng xử lý bản địa hóa sau, bạn không cần tự sáng tạo ở đây.

Trả lời CHỈ bằng JSON, format:
{{"translations": [{{"id": <id câu>, "text": "<bản dịch>"}}]}}
"""


def translate(segments: List[Segment], source_lang: str, target_lang: str, genre: str) -> List[Segment]:
    system_prompt = SYSTEM_PROMPT_TMPL.format(
        source_lang=source_lang, target_lang=target_lang, genre=genre or "đời thường"
    )

    for start in range(0, len(segments), BATCH_SIZE):
        batch = segments[start:start + BATCH_SIZE]
        lines = []
        for s in batch:
            tag = "[NHAY_VAN_HOA] " if s.is_culture_sensitive else ""
            lines.append(f"[{s.id}] {tag}{s.source_text}")
        user_prompt = "\n".join(lines)

        result = generate_json(system_prompt, user_prompt)
        translated = {t["id"]: t["text"] for t in result.get("translations", [])}

        for s in batch:
            if s.id in translated:
                s.literal_translation = translated[s.id]

    return segments
