import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from yap.alembic.utils import DEFAULT_PG_URL


engine = create_engine(os.getenv("PG_URL", DEFAULT_PG_URL), connect_args={})

session_factory = sessionmaker(autocommit=False, bind=engine)


def get_db():
    db = session_factory()
    try:
        yield db
    finally:
        db.close()
