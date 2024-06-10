import base64
import yap.schema as schema
import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from yap.dependencies import get_db, get_photo_repo
from yap.adapters.photo_repository import PhotoRepository, YA_ART_SOURCE_BUCKET
from yap.router.api import CreateGenerationRequest, Generation
from yap.mapper.generation import map_generation_model


generation_router = APIRouter()


@generation_router.get("/api/generations")
def list_generations(db: Session = Depends(get_db)) -> list[Generation]:
    sessionModels = db.query(schema.Generation).all()
    return list(map(map_generation_model, sessionModels))


@generation_router.post("/api/generations")
def launch_generation(
    request: CreateGenerationRequest,
    photo_repo: PhotoRepository = Depends(get_photo_repo),
    db: Session = Depends(get_db),
) -> Generation:
    img_encoded = request.input_image.split('base64,')[1]
    img_decoded = base64.b64decode(img_encoded)
    image_uuid = uuid.uuid4()

    res = photo_repo.upload_photo(YA_ART_SOURCE_BUCKET, image_uuid, 'jpeg', img_decoded)
    generation = schema.Generation(
        uid=uuid.uuid4(),
        status=schema.GenerationStatus.created,
        input_img_path=request.input_image,
        input_prompt=request.input_prompt,
    )
    res: Generation
    with session.begin() as session:
        db.add(generation)
        db.flush()
        res = map_generation_model(db.query(schema.Generation).where(Generation.uid == generation.uid).one())

    return res