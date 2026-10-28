from typing import Optional
from pydantic import BaseModel, Field
from database.models import JobStatus

class SnapshotResponse(BaseModel):
    job_id: str
    status: JobStatus = JobStatus.PENDING

class StatusResponse(BaseModel):
    job_id: str
    status: JobStatus
    result_url: Optional[str] = None
    error: Optional[str] = None

class Keypoint(BaseModel):
    x: float; y: float; z: float = 0.0; visibility: float = 1.0

class LiveFrame(BaseModel):
    """WS message: client sends landmarks only (no video leaves the device)."""
    keypoints: list[Keypoint] = Field(min_length=33, max_length=33)
    garment_id: Optional[str] = None
