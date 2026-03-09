from enum import Enum
from typing import Optional

from pydantic import BaseModel


class JobStatus(str, Enum):
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Job(BaseModel):
    job_id: str
    status: JobStatus
    video_url: Optional[str] = None
    error: Optional[str] = None
    stage: Optional[str] = None
