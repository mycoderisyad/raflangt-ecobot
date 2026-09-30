"""JSON API that replaces the server-rendered admin panel."""

import logging

import psycopg2
from fastapi import APIRouter, HTTPException, Query, Response, status

from src.api.auth import AdminDep
from src.api.schemas import (
    BroadcastRequest,
    BroadcastResult,
    LocationCreate,
    LocationOut,
    LocationPatch,
    ReportResult,
    ScheduleCreate,
    ScheduleOut,
    SchedulePatch,
    SettingsOut,
    UserCreate,
    UserList,
    UserOut,
    UserPatch,
)
from src.config import get_settings
from src.services.admin import AdminService
from src.services.report import ReportService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["admin"], dependencies=[])
service = AdminService()


@router.get("/dashboard")
def dashboard(admin: AdminDep) -> dict:
    return service.dashboard()


@router.get("/analytics")
def analytics(admin: AdminDep) -> dict:
    return service.analytics()


@router.get("/users", response_model=UserList)
def list_users(
    admin: AdminDep,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> UserList:
    users, total = service.list_users(limit, offset)
    return UserList(users=users, total=total, limit=limit, offset=offset)


@router.post("/users", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(body: UserCreate, admin: AdminDep) -> UserOut:
    try:
        return UserOut(**service.create_user(body.model_dump()))
    except psycopg2.errors.UniqueViolation as exc:
        raise HTTPException(status_code=409, detail="user_id sudah terdaftar") from exc


@router.get("/users/{user_id}", response_model=UserOut)
def get_user(user_id: str, admin: AdminDep) -> UserOut:
    user = service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Pengguna tidak ditemukan")
    return UserOut(**user)


@router.patch("/users/{user_id}", response_model=UserOut)
def patch_user(user_id: str, body: UserPatch, admin: AdminDep) -> UserOut:
    user = service.patch_user(user_id, body.model_dump(exclude_unset=True))
    if not user:
        raise HTTPException(status_code=404, detail="Pengguna tidak ditemukan")
    return UserOut(**user)


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: str, admin: AdminDep) -> Response:
    try:
        if not service.delete_user(user_id):
            raise HTTPException(status_code=404, detail="Pengguna tidak ditemukan")
    except psycopg2.IntegrityError as exc:
        raise HTTPException(
            status_code=409,
            detail="Pengguna memiliki riwayat terkait; nonaktifkan melalui PATCH",
        ) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/locations", response_model=list[LocationOut])
def list_locations(admin: AdminDep) -> list[LocationOut]:
    return [LocationOut(**row) for row in service.list_locations()]


@router.post(
    "/locations", response_model=LocationOut, status_code=status.HTTP_201_CREATED
)
def create_location(body: LocationCreate, admin: AdminDep) -> LocationOut:
    try:
        return LocationOut(**service.create_location(body.model_dump()))
    except psycopg2.IntegrityError as exc:
        raise HTTPException(
            status_code=409, detail="Titik pengumpulan tidak dapat dibuat"
        ) from exc


@router.get("/locations/{location_id}", response_model=LocationOut)
def get_location(location_id: str, admin: AdminDep) -> LocationOut:
    location = service.get_location(location_id)
    if not location:
        raise HTTPException(status_code=404, detail="Lokasi tidak ditemukan")
    return LocationOut(**location)


@router.patch("/locations/{location_id}", response_model=LocationOut)
def patch_location(
    location_id: str, body: LocationPatch, admin: AdminDep
) -> LocationOut:
    location = service.patch_location(location_id, body.model_dump(exclude_unset=True))
    if not location:
        raise HTTPException(status_code=404, detail="Lokasi tidak ditemukan")
    return LocationOut(**location)


@router.delete("/locations/{location_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_location(location_id: str, admin: AdminDep) -> Response:
    if not service.delete_location(location_id):
        raise HTTPException(status_code=404, detail="Lokasi tidak ditemukan")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/schedules", response_model=list[ScheduleOut])
def list_schedules(admin: AdminDep) -> list[ScheduleOut]:
    return [ScheduleOut(**row) for row in service.list_schedules()]


@router.post(
    "/schedules", response_model=ScheduleOut, status_code=status.HTTP_201_CREATED
)
def create_schedule(body: ScheduleCreate, admin: AdminDep) -> ScheduleOut:
    return ScheduleOut(**service.create_schedule(body.model_dump()))


@router.get("/schedules/{schedule_id}", response_model=ScheduleOut)
def get_schedule(schedule_id: int, admin: AdminDep) -> ScheduleOut:
    schedule = service.get_schedule(schedule_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="Jadwal tidak ditemukan")
    return ScheduleOut(**schedule)


@router.patch("/schedules/{schedule_id}", response_model=ScheduleOut)
def patch_schedule(
    schedule_id: int, body: SchedulePatch, admin: AdminDep
) -> ScheduleOut:
    schedule = service.patch_schedule(schedule_id, body.model_dump(exclude_unset=True))
    if not schedule:
        raise HTTPException(status_code=404, detail="Jadwal tidak ditemukan")
    return ScheduleOut(**schedule)


@router.delete("/schedules/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_schedule(schedule_id: int, admin: AdminDep) -> Response:
    if not service.delete_schedule(schedule_id):
        raise HTTPException(status_code=404, detail="Jadwal tidak ditemukan")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/broadcast/audience")
def broadcast_audience(admin: AdminDep) -> dict[str, int]:
    return {"eligible": service.broadcast_audience()}


@router.post("/broadcast", response_model=BroadcastResult)
def broadcast(body: BroadcastRequest, admin: AdminDep) -> BroadcastResult:
    settings = get_settings()
    if not settings.telegram.enabled or not settings.telegram.bot_token:
        raise HTTPException(status_code=503, detail="Integrasi Telegram belum aktif")
    return BroadcastResult(**service.broadcast(body.message))


@router.post("/reports/send", response_model=ReportResult)
def send_report(admin: AdminDep) -> ReportResult:
    result = ReportService().generate_and_send()
    if result.get("success"):
        return ReportResult(
            success=True, message="Laporan berhasil dikirim ke email tujuan"
        )
    logger.error("Report delivery failed: %s", result.get("error"))
    return ReportResult(
        success=False,
        message="Laporan gagal dikirim; periksa konfigurasi email dan log server",
    )


@router.get("/settings", response_model=SettingsOut)
def settings_view(admin: AdminDep) -> SettingsOut:
    cfg = get_settings()
    database_name = cfg.database.url.rsplit("/", 1)[-1].split("?", 1)[0]
    return SettingsOut(
        name=cfg.app.name,
        version=cfg.app.version,
        environment=cfg.app.environment,
        database=f"PostgreSQL ({database_name})",
        ai_provider=cfg.ai.provider,
        village_name=cfg.app.village_name or None,
        telegram_enabled=cfg.telegram.enabled,
        telegram_mode=cfg.telegram.mode,
    )
