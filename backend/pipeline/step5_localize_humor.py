"""
Bước 5: Bản địa hóa hài/chơi chữ (pass 2 — "hay" và phù hợp văn hóa).

Chỉ áp dụng cho các segment có is_culture_sensitive=True (từ bước 3).
Đây là lý do vì sao bước 3 và 4 phải tách riêng: nếu gộp "dịch đúng" và
"sáng tạo lại cho hài" vào cùng 1 lần gọi LLM, chất lượng thường không ổn định.

Xử lý TỪNG segment riêng lẻ (không batch) kèm vài câu ngữ cảnh xung quanh,
vì mỗi câu đùa cần được cân nhắc kỹ lưỡng hơn là xử lý hàng loạt.
"""
from typing import List
from ..models import Segment
from ..llm_client import generate

SYSTEM_PROMPT_TMPL = """Bạn là biên tập viên bản địa hóa nội dung (localization editor)
cho khán giả nói tiếng {target_lang}, có hiểu biết sâu về văn hóa, hài kịch và
ngôn ngữ đời thường của khán giả đích.

Nhiệm vụ: viết lại câu được đánh dấu ĐÍCH sao cho:
- Giữ đúng CHỨC NĂNG của câu gốc (nếu là câu đùa → phải gây cười; nếu là chơi chữ
  → phải có yếu tố chơi chữ tương đương trong tiếng {target_lang}), không cần giữ
  nghĩa đen nếu nghĩa đen làm mất tác dụng gây cười.
- Tìm TƯƠNG ĐƯƠNG VĂN HÓA: nếu câu gốc nhắc đến người/sự kiện/meme mà khán giả đích
  không biết, có thể thay bằng người/sự kiện/meme tương đương quen thuộc với khán giả đích.
- Độ dài câu viết lại nên gần với độ dài câu gốc (tính theo số âm tiết khi đọc),
  để khi lồng tiếng không bị lệch quá nhiều so với thời lượng gốc.
- Giữ văn phong phù hợp thể loại nội dung: {genre}.

Chỉ trả lời đúng 1 dòng là câu đã viết lại, không giải thích, không thêm ký hiệu nào khác.
"""


def localize(segments: List[Segment], target_lang: str, genre: str) -> List[Segment]:
    system_prompt = SYSTEM_PROMPT_TMPL.format(target_lang=target_lang, genre=genre or "đời thường")

    flagged = [s for s in segments if s.is_culture_sensitive]
    for s in flagged:
        context = _context_window(segments, s.id, window=1)
        user_prompt = (
            f"Ngữ cảnh xung quanh:\n{context}\n\n"
            f"Lý do câu này được đánh dấu nhạy văn hóa: {s.culture_note or 'không rõ'}\n\n"
            f"Câu ĐÍCH cần viết lại: \"{s.source_text}\"\n"
            f"(Bản dịch sát nghĩa tham khảo, KHÔNG bắt buộc giữ nguyên: \"{s.literal_translation or ''}\")"
        )
        rewritten = generate(system_prompt, user_prompt).strip().strip('"')
        s.localized_translation = rewritten

    return segments


def _context_window(segments: List[Segment], center_id: int, window: int = 1) -> str:
    lo, hi = center_id - window, center_id + window
    lines = [f"[{s.id}] {s.source_text}" for s in segments if lo <= s.id <= hi]
    return "\n".join(lines)
