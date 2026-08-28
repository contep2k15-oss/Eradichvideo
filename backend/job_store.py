import json
import os
import uuid
from typing import Optional

from .config import settings
from .models import Job


def _job_dir(job_id: str) -> str:
    d = os.path.join(settings.JOBS_DIR, job_id)
    os.makedirs(d, exist_ok=True)
    return d


def _job_file(job_id: str) -> str:
    return os.path.join(_job_dir(job_id), "job.json")


def create_job(**kwargs) -> Job:
    job_id = uuid.uuid4().hex[:12]
    job = Job(id=job_id, **kwargs)
    save_job(job)
    return job


def save_job(job: Job) -> None:
    with open(_job_file(job.id), "w", encoding="utf-8") as f:
        f.write(job.model_dump_json(indent=2))


def load_job(job_id: str) -> Optional[Job]:
    path = _job_file(job_id)
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return Job(**data)


def list_jobs() -> list:
    if not os.path.isdir(settings.JOBS_DIR):
        return []
    out = []
    for job_id in os.listdir(settings.JOBS_DIR):
        job = load_job(job_id)
        if job:
            out.append(job)
    return sorted(out, key=lambda j: j.id, reverse=True)
