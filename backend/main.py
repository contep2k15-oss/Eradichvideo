import os
import shutil
from typing import List, Optional

from fastapi import FastAPI, UploadFile, File, Form, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from .config import settings
from .models import Job, JobStatus
from . import job_store
from . import pipeline_runner

app = FastAPI(title="Tool Dịch Video Đa Ngôn Ngữ")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- Bước 1: tạo job (nhận link hoặc file upload) ----------

@app.post("/api/jobs")
async def create_job(
    background_tasks: BackgroundTasks,
    target_lang: str = Form(...),
    source_lang: Optional[str] = Form(None),
    content_genre: Optional[str] = Form(None),
    source_url: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
):
    if not source_url and not file:
        raise HTTPException(400, "Cần cung cấp source_url hoặc upload file video")

    job = job_store.create_job(
        target_lang=target_lang,
        source_lang=source_lang,
        content_genre=content_genre,
        source_url=source_url,
    )

    if file:
        jd = os.path.join(settings.JOBS_DIR, job.id)
        os.makedirs(jd, exist_ok=True)
        ext = os.path.splitext(file.filename)[1] or ".mp4"
        dest = os.path.join(jd, f"source{ext}")
        with open(dest, "wb") as f:
            shutil.copyfileobj(file.file, f)
        job.source_file = dest
        job_store.save_job(job)

    background_tasks.add_task(_run_until_review_bg, job.id)
    return {"job_id": job.id, "status": job.status}


async def _run_until_review_bg(job_id: str):
    job = job_store.load_job(job_id)
    await pipeline_runner.run_until_review(job)


# ---------- Theo dõi tiến trình ----------

@app.get("/api/jobs/{job_id}")
async def get_job(job_id: str):
    job = job_store.load_job(job_id)
    if not job:
        raise HTTPException(404, "Không tìm thấy job")
    return job


@app.get("/api/jobs")
async def get_jobs():
    return job_store.list_jobs()


# ---------- Bước 7: review con người ----------

class SegmentEdit(BaseModel):
    id: int
    edited_text: str


class ReviewSubmission(BaseModel):
    edits: List[SegmentEdit] = []


@app.get("/api/jobs/{job_id}/review")
async def get_review_data(job_id: str):
    """Trả về danh sách segment để hiển thị UI review, ưu tiên đoạn cần chú ý lên đầu
    (đã đánh dấu nhạy văn hóa HOẶC bị QA cảnh báo lệch nghĩa)."""
    job = job_store.load_job(job_id)
    if not job:
        raise HTTPException(404, "Không tìm thấy job")
    if job.status != JobStatus.AWAITING_REVIEW:
        raise HTTPException(400, f"Job chưa sẵn sàng để review (trạng thái hiện tại: {job.status})")

    segments = sorted(
        job.segments,
        key=lambda s: (not (s.is_culture_sensitive or s.qa_flag), s.id),
    )
    return segments


@app.post("/api/jobs/{job_id}/review")
async def submit_review(job_id: str, submission: ReviewSubmission, background_tasks: BackgroundTasks):
    job = job_store.load_job(job_id)
    if not job:
        raise HTTPException(404, "Không tìm thấy job")
    if job.status != JobStatus.AWAITING_REVIEW:
        raise HTTPException(400, f"Job chưa ở trạng thái chờ review (hiện tại: {job.status})")

    edit_map = {e.id: e.edited_text for e in submission.edits}
    for s in job.segments:
        if s.id in edit_map:
            s.human_edited_text = edit_map[s.id]

    job_store.save_job(job)
    background_tasks.add_task(_run_after_review_bg, job.id)
    return {"job_id": job.id, "status": "processing_after_review"}


async def _run_after_review_bg(job_id: str):
    job = job_store.load_job(job_id)
    await pipeline_runner.run_after_review(job)


# ---------- Tải kết quả ----------

@app.get("/api/jobs/{job_id}/download/final")
async def download_final(job_id: str):
    job = job_store.load_job(job_id)
    if not job or not job.final_video_path or not os.path.exists(job.final_video_path):
        raise HTTPException(404, "Chưa có video hoàn chỉnh")
    return FileResponse(job.final_video_path, filename=f"{job_id}_final.mp4")


@app.get("/api/jobs/{job_id}/download/{platform}")
async def download_platform_export(job_id: str, platform: str):
    job = job_store.load_job(job_id)
    if not job or platform not in job.export_paths:
        raise HTTPException(404, "Không tìm thấy bản xuất cho nền tảng này")
    path = job.export_paths[platform]
    if not os.path.exists(path):
        raise HTTPException(404, "File xuất không tồn tại trên đĩa")
    return FileResponse(path, filename=f"{job_id}_{platform}.mp4")


@app.get("/api/jobs/{job_id}/download/subtitle")
async def download_subtitle(job_id: str):
    job = job_store.load_job(job_id)
    if not job or not job.subtitle_path or not os.path.exists(job.subtitle_path):
        raise HTTPException(404, "Chưa có file phụ đề")
    return FileResponse(job.subtitle_path, filename=f"{job_id}.srt")


# ---------- Phục vụ giao diện web tĩnh ----------
frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.isdir(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
