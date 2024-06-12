from datetime import datetime
from http import HTTPStatus
import uuid
import yap.router.api as yapi
import yap.mapper.generation as mapper
from yap.schema import Generation, GenerationResult, GenerationStatus


def sample_generation() -> Generation:
    gen = Generation()
    gen.uid = uuid.uuid4()
    gen.status = GenerationStatus.finished
    gen.created_at = datetime.now()
    gen.meta = {}
    gen.input_img_path = "img-in"
    gen.description = "description"

    gen_result = GenerationResult()
    gen_result.uid = uuid.uuid4()
    gen_result.started_at = datetime.now()
    gen_result.finished_at = datetime.now()
    gen_result.img_path = "img-res"
    gen_result.generation = gen

    gen.results.append(gen_result)
    return gen


def test_list(api_client, orm_session):
    orm_session.add(sample_generation())
    orm_session.commit()

    response = api_client.get("/api/generations")
    assert response.status_code == HTTPStatus.OK

    data = response.json()
    assert len(data) == 1


def test_get_one(api_client, orm_session):
    sample_gen = sample_generation()
    orm_session.add(sample_gen)
    orm_session.commit()

    response = api_client.get(f"/api/generations/{str(sample_gen.uid)}")
    assert response.status_code == HTTPStatus.OK

    data = response.json()
    generation = yapi.Generation(**data)
    assert generation == mapper.map_generation_model(sample_gen)


def test_create(api_client, orm_session, encoded_img: str):
    res = api_client.post(
        "/api/generations",
        json={
            "input_image": encoded_img,
            "description": "Стул",
            "input_prompt": None,
            "negative_prompt": None,
        },
    )

    assert res.status_code == 200
    data = res.json()
    assert data != None
