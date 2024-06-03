from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from yap.orm import get_db
from yap.router.api import Generation
from yap.usecase.generation import get_generations


generation_router = APIRouter()


@generation_router.get("/api/generations")
def list_generations(db: Session = Depends(get_db)) -> list[Generation]:
    return get_generations(db)
