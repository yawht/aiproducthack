import yap.schema as schema

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from yap.orm import get_db
from yap.router.api import Generation
from yap.mapper.generation import map_generation_model


generation_router = APIRouter()


@generation_router.get("/api/generations")
def list_generations(db: Session = Depends(get_db)) -> list[Generation]:
    sessionModels = db.query(schema.Generation).all()
    return list(map(map_generation_model, sessionModels))
