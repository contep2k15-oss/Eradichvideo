from enum import Enum
from typing import List, Optional
from pydantic import BaseModel


class JobStatus(str, Enum):
    CREATED = "created"
    EXTRACTING = "extracting"           # bước 1-2
    DETECTING_CULTURE = "detecting_culture"  # bước 3
    TRANSLATING = "translating"         # bước 4
    LOCALIZING_HUMOR = "localizing_humor"  # bước 5
    QA_CHECKING = "qa_checking"         # bước 6
    AWAITING_REVIEW = "awaiting_review"  # bước 7 (dừng lại chờ người duyệt)
    SYNTHESIZING_VOICE = "synthesizing_voice"  # bước 8
    SYNCING_TIMING = "syncing_timing"   # bước 9
    BUILDING_SUBTITLES = "building_subtitles"  # bước 10
    MUXING = "muxing"                   # bước 11
    EXPORTING = "exporting"             # bước 12
    DONE = "done"
    FAILED = "failed"


class Segment(BaseModel):
    """Một đơn vị dịch nhỏ nhất: 1 câu/cụm từ có timestamp, do ASR sinh ra."""
    id: int
    start: float          # giây
    end: float             # giây
    source_text: str

    # gắn cờ ở bước 3 nếu đoạn này chứa yếu tố nhạy văn hóa (hài/chơi chữ/thành ngữ...)
    is_culture_sensitive: bool = False
    culture_note: Optional[str] = None  # LLM giải thích vì sao đoạn này nhạy

    # bước 4: dịch sát nghĩa
    literal_translation: Optional[str] = None

    # bước 5: bản địa hóa (chỉ khác literal_translation nếu is_culture_sensitive=True)
    localized_translation: Optional[str] = None

    # bước 6: kết quả QA dịch ngược
    back_translation: Optional[str] = None
    qa_flag: bool = False       # True nếu back-translation lệch nghĩa đáng kể
    qa_note: Optional[str] = None

    # bước 7: người dùng có thể sửa tay đè lên bản dịch cuối
    human_edited_text: Optional[str] = None

    @property
    def final_text(self) -> str:
        return (
            self.human_edited_text
            or self.localized_translation
            or self.literal_translation
            or self.source_text
        )


class Job(BaseModel):
    id: str
    source_url: Optional[str] = None
    source_file: Optional[str] = None
    source_lang: Optional[str] = None
    target_lang: str
    content_genre: Optional[str] = None  # hài / trang trọng / giáo dục / đời thường

    status: JobStatus = JobStatus.CREATED
    error: Optional[str] = None

    segments: List[Segment] = []

    # đường dẫn file trung gian/đầu ra
    raw_video_path: Optional[str] = None
    raw_audio_path: Optional[str] = None
    dubbed_audio_path: Optional[str] = None
    subtitle_path: Optional[str] = None
    final_video_path: Optional[str] = None
    export_paths: dict = {}   # {"youtube": path, "tiktok": path, ...}
