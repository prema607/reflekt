from datetime import datetime, timezone
from enum import Enum
from typing import Annotated, Optional
from bson import ObjectId
from pydantic import BaseModel, BeforeValidator, ConfigDict, Field

PyObjectId = Annotated[str, BeforeValidator(lambda v: str(v) if isinstance(v, ObjectId) else v)]
now = lambda: datetime.now(timezone.utc)

class Slot(str, Enum):
    UPPER_BODY = "UPPER_BODY"; LOWER_BODY = "LOWER_BODY"
    FULL_BODY = "FULL_BODY"; ACCESSORY_OVERLAY = "ACCESSORY_OVERLAY"

class TargetAudience(str, Enum):  # scales to men/kids with no migration
    WOMEN = "women"; MEN = "men"; KIDS = "kids"

class ApparelType(str, Enum):
    WESTERN = "western"; ETHNIC = "ethnic"

class JobStatus(str, Enum):
    PENDING = "PENDING"; PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"; FAILED = "FAILED"

class GarmentComponent(BaseModel):
    name: str                      # Blouse / Skirt / Dupatta
    slot: Slot
    image_url: str
    opacity: float = Field(1.0, ge=0.3, le=1.0)  # sheer fabrics 0.3-0.7

class GarmentModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    id: Optional[PyObjectId] = Field(None, alias="_id")
    name: str
    target_audience: TargetAudience = TargetAudience.WOMEN
    apparel_type: ApparelType
    category: str                  # saree, lehenga, anarkali, kurti, dress...
    components: list[GarmentComponent] = Field(min_length=1, max_length=3)
    sizes: list[str] = ["S", "M", "L", "XL", "XXL", "3XL"]
    created_at: datetime = Field(default_factory=now)

class UserModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    id: Optional[PyObjectId] = Field(None, alias="_id")
    firebase_uid: str
    email: Optional[str] = None
    created_at: datetime = Field(default_factory=now)

class TryOnSessionModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    id: Optional[PyObjectId] = Field(None, alias="_id")
    user_id: str
    garment_ids: list[str]
    person_image_url: str
    status: JobStatus = JobStatus.PENDING
    landmarks: Optional[list[dict]] = None   # 33 MediaPipe keypoints
    result_url: Optional[str] = None
    error: Optional[str] = None
    created_at: datetime = Field(default_factory=now)
    updated_at: datetime = Field(default_factory=now)
