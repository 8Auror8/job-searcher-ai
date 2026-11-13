"""CV versions and search preferences."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Request, Response, UploadFile, status

from app.api.deps import CurrentUser, SessionDep, SettingsDep, get_cv_extractor
from app.core.rate_limit import limiter
from app.models import CvVersion
from app.schemas.cv import (
    CvBlankIn,
    CvOut,
    CvPatchIn,
    CvProfile,
    CvSummaryOut,
    Origin,
    PreferencesData,
)
from app.services.cv_extraction import CvExtractor
from app.services.cv_service import CvService
from app.services.documents import MAX_FILE_BYTES, FileTooLarge

router = APIRouter(tags=["cvs"])


def get_cv_service(
    session: SessionDep,
    user: CurrentUser,
    settings: SettingsDep,
    extractor: Annotated[CvExtractor | None, Depends(get_cv_extractor)],
) -> CvService:
    return CvService(session, user, extractor, settings.ai_daily_calls_per_user)


ServiceDep = Annotated[CvService, Depends(get_cv_service)]


def _summary(cv: CvVersion) -> CvSummaryOut:
    return CvSummaryOut(
        id=cv.id,
        name=cv.name,
        origin=cv.origin,
        is_primary=cv.is_primary,
        archived=cv.archived_at is not None,
        extraction_status=cv.extraction_status,
        created_at=cv.created_at,
        updated_at=cv.updated_at,
    )


def _full(cv: CvVersion) -> CvOut:
    return CvOut(
        **_summary(cv).model_dump(),
        profile=CvProfile.model_validate(cv.profile or {}),
        extraction_notes=cv.extraction_notes or {},
        has_source_text=bool(cv.source_text),
    )


@router.get("/cvs")
async def list_cvs(service: ServiceDep, include_archived: bool = False) -> list[CvSummaryOut]:
    return [_summary(cv) for cv in await service.list(include_archived)]


@router.post("/cvs", status_code=status.HTTP_201_CREATED)
@limiter.limit("10/hour")
async def upload_cv(
    request: Request,
    service: ServiceDep,
    file: Annotated[UploadFile, File(description="PDF or DOCX, max 5 MB")],
    consent: Annotated[bool, Form()] = False,
    origin: Annotated[Origin, Form()] = "upload",
    name: Annotated[str | None, Form(max_length=100)] = None,
) -> CvOut:
    data = await file.read(MAX_FILE_BYTES + 1)
    if len(data) > MAX_FILE_BYTES:
        raise FileTooLarge()
    cv = await service.create_from_file(data, name, origin, consent)
    return _full(cv)


@router.post("/cvs/blank", status_code=status.HTTP_201_CREATED)
async def create_blank_cv(body: CvBlankIn, service: ServiceDep) -> CvOut:
    return _full(await service.create_blank(body.name))


@router.get("/cvs/{cv_id}")
async def get_cv(cv_id: uuid.UUID, service: ServiceDep) -> CvOut:
    return _full(await service.get(cv_id))


@router.patch("/cvs/{cv_id}")
async def patch_cv(cv_id: uuid.UUID, body: CvPatchIn, service: ServiceDep) -> CvOut:
    cv = await service.update(cv_id, body.name, bool(body.is_primary), body.archived)
    return _full(cv)


@router.put("/cvs/{cv_id}/profile")
async def put_profile(cv_id: uuid.UUID, body: CvProfile, service: ServiceDep) -> CvOut:
    return _full(await service.update_profile(cv_id, body))


@router.post("/cvs/{cv_id}/extract")
@limiter.limit("10/hour")
async def reextract_cv(request: Request, cv_id: uuid.UUID, service: ServiceDep) -> CvOut:
    return _full(await service.reextract(cv_id))


@router.delete("/cvs/{cv_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_cv(cv_id: uuid.UUID, service: ServiceDep) -> Response:
    await service.delete(cv_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/preferences")
async def get_preferences(service: ServiceDep) -> PreferencesData:
    return await service.get_preferences()


@router.put("/preferences")
async def put_preferences(body: PreferencesData, service: ServiceDep) -> PreferencesData:
    return await service.save_preferences(body)
