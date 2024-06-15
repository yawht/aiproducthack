import io
import logging
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
    description: str


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
        filedata = io.BytesIO(inp.image_bytes)
        headers = {
            "accept": "image/*",
        }

        if settings.yc_oauth_token is not None:
            iam_token = get_iam_token()
            headers["Authorization"] = f"Bearer {iam_token}"
            headers["x-node-id"] = settings.yc_node_id
            headers["x-folder-id"] = settings.yc_folder_id

        files = {
            "image": (f"image.{inp.extension}", filedata),
            "description": (None, inp.description),
            "positive_prompt": (None, inp.prompt or ""),
            "negative_prompt": (None, settings.bento_negative_prompt),
            "num_inference_steps": (None, settings.bento_inference_steps),
        }

        response = requests.post(
            url=settings.bento_url, headers=headers, files=files, timeout=(15, settings.bento_timeout_sec)
        )

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
            generation_obj = session.query(schema.Generation).get(generation_request_id)
            bucket, object_name = generation_obj.input_img_path.split("/")

            raw_input_bytes = self.photo_repository.get_photo(bucket, object_name)
            model_data = InpainterInput(
                image_bytes=raw_input_bytes,
                extension=object_name.split(".")[-1],
                prompt=generation_obj.input_prompt,
                description=generation_obj.description or "",
            )

            generation_obj.status = schema.GenerationStatus.in_progress
            session.commit()

        gen_result_id = uuid.uuid4()
        result = schema.GenerationResult(
            uid=gen_result_id,
            started_at=started_at,
            generation_id=generation_request_id,
        )
        generated = None
        gen_err = None
        try:
            generated = self._inpainter.process(model_data)
        except Exception as err:
            logging.error("Failed to generate photo: ", err)
            gen_err = str(err)

        with self.new_session() as session:
            generation_obj = session.query(schema.Generation).get(generation_request_id)
            if generated is not None:
                logging.info("Generation successfull")
                filename = f"{gen_result_id}.{generated.filetype}"
                result.img_path = f"{INPAINTER_GEN_BUCKET}/{filename}"
                self.photo_repository.upload_photo(
                    INPAINTER_GEN_BUCKET,
                    filename,
                    generated.filetype,
                    generated.image,
                )
                generation_obj.status = schema.GenerationStatus.finished
            else:
                result.error = gen_err
                generation_obj.status = schema.GenerationStatus.failed

            session.add(result)
            session.flush()
            session.commit()


@celery_app.task(base=InpaintPhoto, bind=True, name="inpaint_photo")
def inpaint_photo(self: InpaintPhoto, generation_request_id: uuid.UUID):
    return self.execute(generation_request_id)
