from sqlalchemy.orm import Session
from yap.router.api import Generation
from yap.schema import Generation as GenerationModel


def get_generations(session: Session) -> list[Generation]:
    return session.query(GenerationModel).all()
