from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.core.params import POSTGRES_INT_MAX


class EnrollmentRead(BaseModel):
    id: int
    user_id: int
    course_id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class EnrollmentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_id: int = Field(..., gt=0, le=POSTGRES_INT_MAX)
    course_id: int = Field(..., gt=0, le=POSTGRES_INT_MAX)
