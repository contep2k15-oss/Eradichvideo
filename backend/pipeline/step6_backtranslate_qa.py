"""
Bước 6: Kiểm tra ngược (back-translation QA).

Dịch ngược bản dịch cuối (localized nếu có, literal nếu không) về ngôn ngữ gốc,
rồi nhờ LLM tự so sánh với câu gốc để phát hiện lệch nghĩa NGHIÊM TRỌNG
(không phải lệch văn phong — vì với các câu đã bản địa hóa hài, lệch văn phong
là CHỦ ĐÍCH, chỉ cần cảnh báo khi ý nghĩa cốt lõi/thông tin quan trọng bị sai).

Các segment bị qa_flag=True sẽ được ưu tiên hiển thị lên đầu ở bước 7 (review).
"""
from typing import List
from ..models import Segment
from ..llm_client import generate_json

BATCH_SIZE = 15

SYSTEM_PROMPT = """Bạn kiểm tra chất lượng dịch thuật bằng phương pháp back-translation.
Với mỗi cặp câu gốc và câu đã dịch ngược lại, đánh giá xem THÔNG TIN CỐT LÕI có bị
sai lệch nghiêm trọng không (KHÔNG tính lệch văn phong/cách diễn đạt là lỗi — với
câu đã bản địa hóa hài, đổi khác nghĩa đen là bình thường và có chủ đích).

Chỉ đánh dấu flag=true khi: sai sự kiện, đảo ngược ý nghĩa, mất thông tin quan trọng,
hoặc hiểu sai hoàn toàn ngữ cảnh.

Trả lời CHỈ bằng JSON:
{"checks": [{"id": <id>, "flag": true/false, "note": "<lý do ngắn nếu flag=true, để trống nếu false>"}]}
"""


def back_translate(segments: List[Segment], target_lang: str, source_lang: str) -> List[Segment]:
    """Dịch ngược từng câu final (localized ưu tiên hơn literal) về ngôn ngữ gốc."""
    from ..llm_client import generate

    bt_system = (
        f"Dịch câu sau từ tiếng {target_lang} sang tiếng {source_lang}. "
        "Chỉ trả lời đúng 1 dòng là bản dịch, không giải thích."
    )
    for s in segments:
        text = s.localized_translation or s.literal_translation or ""
        if not text:
            continue
        s.back_translation = generate(bt_system, text).strip()

    return segments


def qa_compare(segments: List[Segment]) -> List[Segment]:
    for start in range(0, len(segments), BATCH_SIZE):
        batch = [s for s in segments[start:start + BATCH_SIZE] if s.back_translation]
        if not batch:
            continue

        lines = [
            f"[{s.id}] Câu gốc: \"{s.source_text}\" | Dịch ngược: \"{s.back_translation}\""
            for s in batch
        ]
        user_prompt = "\n".join(lines)

        result = generate_json(SYSTEM_PROMPT, user_prompt)
        checks = {c["id"]: c for c in result.get("checks", [])}

        for s in batch:
            c = checks.get(s.id)
            if c:
                s.qa_flag = bool(c.get("flag", False))
                s.qa_note = c.get("note") or None

    return segments
