import yap.schema as orm
from yap.router.api import Generation, GenerationResult
from yap.settings import settings


def form_image_link(img_path: str) -> str:
    return f'http://{settings.minio_endpoint}/{img_path}'

def map_generation_result_model(model: orm.GenerationResult) -> GenerationResult:
    return GenerationResult(
        uid=model.uid,
        started_at=model.started_at,
        finished_at=model.finished_at,
        error=model.error,
        image_link=form_image_link(model.img_path),
    )


def map_generation_model(model: orm.Generation) -> Generation:
    result_models = model.results
    last_finished_res = max(result_models, key=lambda res: res.finished_at) if result_models else []
    return Generation(
        uid=model.uid,
        status=model.status,
        started_at=model.created_at,
        finished_at=last_finished_res.finished_at if last_finished_res else None,
        metadata=model.meta,
        input_image_link=form_image_link(model.input_img_path),
        input_prompt=model.input_prompt,
        results=list(map(map_generation_result_model, result_models)),
    )
