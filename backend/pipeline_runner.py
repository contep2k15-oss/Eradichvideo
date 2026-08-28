"""
Điều phối toàn bộ 12 bước, ánh xạ đúng theo thiết kế:

1-2  input_extract   -> tải video, tách audio
2b   asr             -> transcript có timestamp (faster-whisper, local GPU)
3    culture_detect  -> đánh dấu đoạn nhạy văn hóa (LLM)
4    translate        -> dịch sát nghĩa (LLM, có context toàn video)
5    localize_humor   -> bản địa hóa riêng cho đoạn đã đánh dấu (LLM)
6    backtranslate_qa -> dịch ngược + so sánh tự động (LLM)
=> DỪNG lại ở đây, chuyển job sang AWAITING_REVIEW (bước 7 do người dùng làm qua UI)
8-12 (gọi tiếp sau khi người dùng submit review) -> TTS, sync, subtitle, mux, export

Chạy nền bằng asyncio task đơn giản (đủ cho công cụ 1 người dùng chạy local;
nếu cần nhiều người dùng đồng thời, thay bằng queue thật như Celery/RQ).
"""
import os
from .config import settings
from .models import Job, JobStatus
from . import job_store
from .pipeline import (
    step1_2_input_extract as step_input,
    step2_asr as step_asr,
    step3_culture_detect as step_culture,
    step4_translate as step_translate,
    step5_localize_humor as step_localize,
    step6_backtranslate_qa as step_qa,
    step8_tts as step_tts,
    step9_sync as step_sync,
    step10_subtitles as step_subs,
    step11_mux as step_mux,
    step12_export as step_export,
)


def _job_dir(job: Job) -> str:
    return os.path.join(settings.JOBS_DIR, job.id)


async def run_until_review(job: Job) -> Job:
    """Chạy bước 1 -> 6, dừng ở AWAITING_REVIEW."""
    jd = _job_dir(job)

    try:
        job.status = JobStatus.EXTRACTING
        job_store.save_job(job)

        if job.source_url and not job.source_file:
            job.raw_video_path = step_input.download_video(job.source_url, jd)
        else:
            job.raw_video_path = job.source_file
        job.raw_audio_path = step_input.extract_audio(job.raw_video_path, jd)

        job.segments = step_asr.transcribe(job.raw_audio_path)

        if not job.content_genre:
            sample = " ".join(s.source_text for s in job.segments[:15])
            job.content_genre = step_input.detect_genre(sample)

        job_store.save_job(job)

        job.status = JobStatus.DETECTING_CULTURE
        job_store.save_job(job)
        job.segments = step_culture.detect(job.segments)
        job_store.save_job(job)

        job.status = JobStatus.TRANSLATING
        job_store.save_job(job)
        job.segments = step_translate.translate(
            job.segments, job.source_lang or "nguồn", job.target_lang, job.content_genre
        )
        job_store.save_job(job)

        job.status = JobStatus.LOCALIZING_HUMOR
        job_store.save_job(job)
        job.segments = step_localize.localize(job.segments, job.target_lang, job.content_genre)
        job_store.save_job(job)

        job.status = JobStatus.QA_CHECKING
        job_store.save_job(job)
        job.segments = step_qa.back_translate(job.segments, job.target_lang, job.source_lang or "nguồn")
        job.segments = step_qa.qa_compare(job.segments)
        job_store.save_job(job)

        job.status = JobStatus.AWAITING_REVIEW
        job_store.save_job(job)

    except Exception as e:
        job.status = JobStatus.FAILED
        job.error = str(e)
        job_store.save_job(job)

    return job


async def run_after_review(job: Job) -> Job:
    """Chạy bước 8 -> 12, gọi sau khi người dùng đã duyệt/sửa xong ở bước 7."""
    jd = _job_dir(job)

    try:
        job.status = JobStatus.SYNTHESIZING_VOICE
        job_store.save_job(job)
        tts_dir = os.path.join(jd, "tts_raw")
        segment_audio_paths = await step_tts.synthesize_segments(job.segments, job.target_lang, tts_dir)

        job.status = JobStatus.SYNCING_TIMING
        job_store.save_job(job)
        synced_dir = os.path.join(jd, "tts_synced")
        synced_paths = step_sync.sync_all(segment_audio_paths, job.segments, synced_dir)

        job.status = JobStatus.BUILDING_SUBTITLES
        job_store.save_job(job)
        job.subtitle_path = step_subs.build_srt(job.segments, jd)
        job_store.save_job(job)

        job.status = JobStatus.MUXING
        job_store.save_job(job)
        total_duration = max((s.end for s in job.segments), default=0)
        dubbed_track = step_mux.build_full_audio_track(synced_paths, job.segments, total_duration, jd)
        job.dubbed_audio_path = dubbed_track
        job.final_video_path = step_mux.mux_final_video(
            job.raw_video_path, dubbed_track, job.subtitle_path, jd
        )
        job_store.save_job(job)

        job.status = JobStatus.EXPORTING
        job_store.save_job(job)
        export_dir = os.path.join(jd, "exports")
        job.export_paths = step_export.export_all(job.final_video_path, export_dir)

        job.status = JobStatus.DONE
        job_store.save_job(job)

    except Exception as e:
        job.status = JobStatus.FAILED
        job.error = str(e)
        job_store.save_job(job)

    return job
