import io
import uuid
from datetime import datetime
from dataclasses import dataclass
from typing import Optional
import requests

from yap.jobs.app import celery_app
from yap.jobs.task_utils import S3TaskMixin, DBTaskMixin

from yap import schema
from yap.settings import settings
from yap.adapters.photo_repository import INPAINTER_GEN_BUCKET


@dataclass
class InpainterInput:
    image_bytes: bytes
    extension: str
    prompt: Optional[str]


@dataclass
class InpainterOutput:
    image: bytes
    filetype: str


def get_iam_token() -> str:
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
    }
    response = requests.post(
        "https://iam.api.cloud.yandex.net/iam/v1/tokens",
        headers=headers,
        json={"yandexPassportOauthToken": settings.yc_oauth_token},
    )
    return response.json()["iamToken"]


class Inpainter:

    # God why...
    def process(self, inp: InpainterInput) -> InpainterOutput:
        iam_token = get_iam_token()
        filedata = io.BytesIO(inp.image_bytes)
        headers = {
            "x-node-alias": "datasphere.user.bento",
            "Authorization": f"Bearer {iam_token}",
            "x-folder-id": "b1gk61tkdst8hqagvopn",
            "accept": "image/*",
        }
        files = {
            "image": (
                f"image.{inp.extension}",
                filedata
            ),
            "prompt": (None, inp.prompt or ""),
            "negative_prompt": (None, settings.bento_negative_prompt),
            "controlnet_conditioning_scale": (None, "0.5"),
            "num_inference_steps": (None, "25"),
        }
        response = requests.post(url=settings.bento_url, headers=headers, files=files, timeout=(15, 50))
        return InpainterOutput(response.content, "jpeg")


class InpaintPhoto(S3TaskMixin, DBTaskMixin, celery_app.Task):
    name = "inpaint_photo"

    def __init__(self):
        self._inpainter = Inpainter()
        self._init_s3()
        super(InpaintPhoto, self).__init__()

    # ошибки обработаем потом

    def execute(self, generation_request_id: uuid.UUID):
        started_at = datetime.now()
        with self.new_session() as session:
            import logging

            generation_obj = session.query(schema.Generation).get(generation_request_id)
            bucket, object_name = generation_obj.input_img_path.split("/")

            raw_input_bytes = self.photo_repository.get_photo(bucket, object_name)
            model_data = InpainterInput(
                image_bytes=raw_input_bytes,
                extension=object_name.split(".")[-1],
                prompt=generation_obj.input_prompt,
            )

            generation_obj.status = schema.GenerationStatus.in_progress
            session.commit()

        generated = self._inpainter.process(model_data)

        gen_result_id = uuid.uuid4()
        filename = f"{gen_result_id}.{generated.filetype}"
        with self.new_session() as session:
            result = schema.GenerationResult(
                uid=gen_result_id,
                started_at=started_at,
                img_path=f"{INPAINTER_GEN_BUCKET}/{filename}",
                generation_id=generation_request_id,
            )
            session.add(result)
            session.flush()
            self.photo_repository.upload_photo(
                INPAINTER_GEN_BUCKET,
                filename,
                generated.filetype,
                generated.image,
            )
            logging.warning("gotten link %r", result.image_link)
            generation_obj = session.query(schema.Generation).get(generation_request_id)
            generation_obj.status = schema.GenerationStatus.finished
            session.commit()


@celery_app.task(base=InpaintPhoto, bind=True, name="inpaint_photo")
def inpaint_photo(self: InpaintPhoto, generation_request_id: uuid.UUID):
    return self.execute(generation_request_id)
