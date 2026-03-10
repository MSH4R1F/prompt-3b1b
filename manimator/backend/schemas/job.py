from enum import Enum

from pydantic import BaseModel


class JobStatus(str, Enum):
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Job(BaseModel):
    job_id: str
    status: JobStatus
    video_url: str | None = None
    error: str | None = None
    stage: str | None = None
