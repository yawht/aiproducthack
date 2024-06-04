from datetime import datetime
from http import HTTPStatus
import uuid
from yap.schema import Generation, GenerationResult, GenerationStatus


def sample_generation() -> Generation:
    gen = Generation()
    gen.uid = uuid.uuid4()
    gen.status = GenerationStatus.finished
    gen.created_at = datetime.now()
    gen.meta = {}
    gen.input_img_path = "img-in"

    gen_result = GenerationResult()
    gen_result.uid = uuid.uuid4()
    gen_result.started_at = datetime.now()
    gen_result.finished_at = datetime.now()
    gen_result.img_path = "img-res"
    gen_result.generation = gen

    gen.results.append(gen_result)
    return gen


def test_get(api_client, orm_session):
    orm_session.add(sample_generation())
    orm_session.commit()

    response = api_client.get("/api/generations")
    assert response.status_code == HTTPStatus.OK

    data = response.json()
    assert len(data) == 1