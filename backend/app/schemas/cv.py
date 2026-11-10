import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.profile import ProfileRead


class CVRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    original_filename: str
    uploaded_at: datetime


class UploadResult(BaseModel):
    cv: CVRead
    profile: ProfileRead
