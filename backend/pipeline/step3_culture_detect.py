"""
Bước 3: Phát hiện điểm "nhạy văn hóa" — câu đùa, chơi chữ, thành ngữ, tục ngữ,
reference văn hóa (tên người nổi tiếng, sự kiện, meme địa phương).

Đây là bước tách riêng QUAN TRỌNG NHẤT trong toàn pipeline: các đoạn được gắn cờ
ở đây sẽ đi qua bước 5 (bản địa hóa) thay vì chỉ dịch sát nghĩa ở bước 4,
và sẽ được ưu tiên đưa vào bước 7 (review con người).

Xử lý theo batch (nhiều segment/lần gọi) thay vì gọi LLM cho từng câu riêng lẻ,
để giảm chi phí API và giữ được ngữ cảnh giữa các câu liền kề.
"""
from typing import List
from ..models import Segment
from ..llm_client import generate_json

BATCH_SIZE = 25  # số segment/lần gọi LLM — cân bằng giữa chi phí và độ chính xác ngữ cảnh

SYSTEM_PROMPT = """Bạn là chuyên gia ngôn ngữ và văn hóa, nhiệm vụ là đọc transcript
video và xác định những câu chứa yếu tố khó dịch trực tiếp sang ngôn ngữ khác, gồm:
- Câu đùa, chơi chữ (wordplay/pun)
- Thành ngữ, tục ngữ
- Reference văn hóa: tên người nổi tiếng, sự kiện, meme, trend địa phương
- Ẩn dụ/châm biếm phụ thuộc ngữ cảnh văn hóa nguồn

Trả lời CHỈ bằng JSON, không thêm text nào khác, theo format:
{"flags": [{"id": <số nguyên id của câu>, "reason": "<giải thích ngắn gọn vì sao câu này nhạy văn hóa>"}]}

Nếu không có câu nào nhạy văn hóa trong batch, trả về {"flags": []}.
"""


def detect(segments: List[Segment]) -> List[Segment]:
    for start in range(0, len(segments), BATCH_SIZE):
        batch = segments[start:start + BATCH_SIZE]
        user_prompt = "\n".join(f"[{s.id}] {s.source_text}" for s in batch)

        result = generate_json(SYSTEM_PROMPT, user_prompt)
        flagged_ids = {f["id"]: f.get("reason", "") for f in result.get("flags", [])}

        for s in batch:
            if s.id in flagged_ids:
                s.is_culture_sensitive = True
                s.culture_note = flagged_ids[s.id]

    return segments
