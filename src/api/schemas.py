"""Public request and response schemas for the HTTP API."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class Role(str, Enum):
    admin = "admin"
    koordinator = "koordinator"
    warga = "warga"


class CollectionPointType(str, Enum):
    fixed = "fixed"
    mobile = "mobile"
    community = "community"


class ScheduleDay(str, Enum):
    senin = "Senin"
    selasa = "Selasa"
    rabu = "Rabu"
    kamis = "Kamis"
    jumat = "Jumat"
    sabtu = "Sabtu"
    minggu = "Minggu"


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1, max_length=200)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class AdminIdentity(BaseModel):
    username: str
    role: str = "admin"


class UserCreate(BaseModel):
    user_id: str = Field(min_length=1, max_length=100, description="Telegram chat ID")
    username: str | None = Field(default=None, max_length=50)
    role: Role = Role.warga
    points: int = Field(default=0, ge=0)
    is_active: bool = True

    @field_validator("user_id")
    @classmethod
    def telegram_private_chat_id(cls, value: str) -> str:
        if not value.isascii() or not value.isdecimal():
            raise ValueError("user_id must be a positive Telegram private chat ID")
        return value


class UserPatch(BaseModel):
    username: str | None = Field(default=None, max_length=50)
    role: Role | None = None
    points: int | None = Field(default=None, ge=0)
    is_active: bool | None = None

    @model_validator(mode="after")
    def reject_null_required_fields(self):
        for key in {"role", "points", "is_active"} & self.model_fields_set:
            if getattr(self, key) is None:
                raise ValueError(f"{key} cannot be null")
        return self


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: str
    username: str | None = None
    name: str | None = None
    role: str
    registration_status: str
    first_seen: datetime | None = None
    last_active: datetime | None = None
    total_messages: int = 0
    total_images: int = 0
    points: int = 0
    is_active: bool = True
    preferences: dict[str, Any] | None = None


class UserList(BaseModel):
    users: list[UserOut]
    total: int
    limit: int
    offset: int


class LocationCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    type: CollectionPointType
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    accepted_waste_types: list[str] = Field(min_length=1)
    schedule: str = Field(min_length=1, max_length=200)
    contact: str | None = Field(default=None, max_length=200)
    description: str | None = Field(default=None, max_length=2000)

    @field_validator("accepted_waste_types")
    @classmethod
    def nonempty_waste_types(cls, value: list[str]) -> list[str]:
        cleaned = [item.strip() for item in value]
        if any(not item for item in cleaned):
            raise ValueError("accepted_waste_types must not contain empty values")
        return cleaned


class LocationPatch(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    type: CollectionPointType | None = None
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    accepted_waste_types: list[str] | None = Field(default=None, min_length=1)
    schedule: str | None = Field(default=None, min_length=1, max_length=200)
    contact: str | None = Field(default=None, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    is_active: bool | None = None

    @model_validator(mode="after")
    def reject_null_required_fields(self):
        for key in {
            "name",
            "type",
            "latitude",
            "longitude",
            "accepted_waste_types",
            "schedule",
            "is_active",
        } & self.model_fields_set:
            if getattr(self, key) is None:
                raise ValueError(f"{key} cannot be null")
        return self


class LocationOut(BaseModel):
    id: str
    name: str
    type: str
    latitude: float
    longitude: float
    accepted_waste_types: list[str]
    schedule: str
    contact: str | None = None
    description: str | None = None
    is_active: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ScheduleCreate(BaseModel):
    location_name: str = Field(min_length=1, max_length=200)
    address: str = Field(min_length=1, max_length=500)
    schedule_day: ScheduleDay
    start_time: str = Field(pattern=r"^([01]\d|2[0-3]):[0-5]\d$")
    end_time: str = Field(pattern=r"^([01]\d|2[0-3]):[0-5]\d$")
    waste_types: list[str] = Field(min_length=1)
    collector: str | None = Field(default=None, max_length=200)
    notes: str | None = Field(default=None, max_length=2000)
    is_active: bool = True

    @field_validator("waste_types")
    @classmethod
    def nonempty_waste_types(cls, value: list[str]) -> list[str]:
        cleaned = [item.strip() for item in value]
        if any(not item for item in cleaned):
            raise ValueError("waste_types must not contain empty values")
        return cleaned


class SchedulePatch(BaseModel):
    location_name: str | None = Field(default=None, min_length=1, max_length=200)
    address: str | None = Field(default=None, min_length=1, max_length=500)
    schedule_day: ScheduleDay | None = None
    start_time: str | None = Field(default=None, pattern=r"^([01]\d|2[0-3]):[0-5]\d$")
    end_time: str | None = Field(default=None, pattern=r"^([01]\d|2[0-3]):[0-5]\d$")
    waste_types: list[str] | None = Field(default=None, min_length=1)
    collector: str | None = Field(default=None, max_length=200)
    notes: str | None = Field(default=None, max_length=2000)
    is_active: bool | None = None

    @model_validator(mode="after")
    def reject_null_required_fields(self):
        required = {
            "location_name",
            "address",
            "schedule_day",
            "start_time",
            "end_time",
            "waste_types",
            "is_active",
        }
        for key in required & self.model_fields_set:
            if getattr(self, key) is None:
                raise ValueError(f"{key} cannot be null")
        return self


class ScheduleOut(BaseModel):
    id: int
    location_name: str
    address: str
    schedule_day: str
    start_time: str
    end_time: str
    waste_types: list[str]
    collector: str | None = None
    notes: str | None = None
    is_active: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None


class BroadcastRequest(BaseModel):
    message: str = Field(min_length=5, max_length=4000)


class BroadcastResult(BaseModel):
    eligible: int
    sent: int
    failed: int


class ReportResult(BaseModel):
    success: bool
    message: str


class SettingsOut(BaseModel):
    name: str
    version: str
    environment: str
    database: str
    ai_provider: str
    village_name: str | None
    telegram_enabled: bool
    telegram_mode: str
