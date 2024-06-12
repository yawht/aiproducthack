import base64
import yap.schema as schema
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from yap.dependencies import get_db, get_photo_repo
from yap.adapters.photo_repository import PhotoRepository, YA_ART_SOURCE_BUCKET
from yap.router.api import CreateGenerationRequest, Generation
from yap.mapper.generation import map_generation_model
from yap.settings import settings


generation_router = APIRouter()


@generation_router.get("/api/generations")
def list_generations(
    page: int = 0, size: int = 50, db: Session = Depends(get_db)
) -> list[Generation]:
    sessionModels = (
        db.query(schema.Generation)
        .order_by(schema.Generation.created_at.desc())
        .limit(settings.generation_list_limit)
        .all()
    )
    return list(map(map_generation_model, sessionModels))


@generation_router.get("/api/generations/{generation_uid}")
def list_generations(generation_uid: str, db: Session = Depends(get_db)) -> Generation:
    uid = uuid.UUID(generation_uid)
    generationModel = (
        db.query(schema.Generation).where(schema.Generation.uid == uid).one_or_none()
    )
    if generationModel is None:
        raise HTTPException(status_code=404, detail="Generation not found")
    return map_generation_model(generationModel)


@generation_router.post("/api/generations")
def launch_generation(
    request: CreateGenerationRequest,
    photo_repo: PhotoRepository = Depends(get_photo_repo),
    db: Session = Depends(get_db),
) -> Generation:

    # God i hate RFC2045
    mime_header, encoded_img = request.input_image.split(",")
    if encoded_img is None:
        raise HTTPException(status_code=400, detail="Invalid image format")
    _, raw_part = mime_header.split("/")
    img_extension, _ = raw_part.split(";")
    if img_extension not in ["jpeg", "png"]:
        raise HTTPException(status_code=400, detail="Invalid image extension")

    img_decoded = base64.b64decode(encoded_img)
    image_uuid = uuid.uuid4()

    res = photo_repo.upload_photo(
        YA_ART_SOURCE_BUCKET, str(image_uuid), img_extension, img_decoded
    )
    generation = schema.Generation(
        uid=uuid.uuid4(),
        status=schema.GenerationStatus.created,
        input_img_path=f"{YA_ART_SOURCE_BUCKET}/{str(image_uuid)}.{img_extension}",
        input_prompt=request.input_prompt,
    )
    db.add(generation)
    db.flush()
    res = map_generation_model(
        db.query(schema.Generation).where(schema.Generation.uid == generation.uid).one()
    )
    db.commit()

    return res
