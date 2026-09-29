from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

NAME_MAX_LENGTH = 80


class UserRead(BaseModel):
    id: int
    first_name: str
    last_name: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UserCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    first_name: str = Field(..., min_length=1, max_length=NAME_MAX_LENGTH)
    last_name: str = Field(..., min_length=1, max_length=NAME_MAX_LENGTH)

    @field_validator("first_name", "last_name", mode="before")
    @classmethod
    def strip_whitespace(cls, value: str) -> str:
        if isinstance(value, str):
            return value.strip()
        return value


class UserUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    first_name: str | None = Field(
        default=None, min_length=1, max_length=NAME_MAX_LENGTH
    )
    last_name: str | None = Field(
        default=None, min_length=1, max_length=NAME_MAX_LENGTH
    )

    @field_validator("first_name", "last_name", mode="before")
    @classmethod
    def strip_whitespace(cls, value: str | None) -> str | None:
        if isinstance(value, str):
            return value.strip()
        return value

    @model_validator(mode="after")
    def reject_null_names(self) -> "UserUpdate":
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided")
        if "first_name" in self.model_fields_set and self.first_name is None:
            raise ValueError("first_name cannot be null")
        if "last_name" in self.model_fields_set and self.last_name is None:
            raise ValueError("last_name cannot be null")
        return self
