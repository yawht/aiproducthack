import uuid
from datetime import datetime
from dataclasses import dataclass
from typing import Optional
import requests

from yap.jobs.app import celery_app
from yap.jobs.task_utils import S3TaskMixin, DBTaskMixin

from yap import schema
from yap.adapters.photo_repository import INPAINTER_GEN_BUCKET


class InpaintPhoto(S3TaskMixin, DBTaskMixin, celery_app.Task):
    name = 'inpaint_photo'
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
            model_data = InpainterInput(
                image_link=generation_obj.image_link,
                prompt=generation_obj.input_prompt,
            )
            session.commit()
        generated = self._inpainter.process(model_data)
        gen_result_id = uuid.uuid4()
        filename = f'{gen_result_id}.{generated.filetype}'
        with self.new_session() as session:
            result = schema.GenerationResult(
                uid=gen_result_id,
                started_at=started_at,
                img_path=f'{INPAINTER_GEN_BUCKET}/{filename}',
                generation_id=generation_request_id,
            )
            session.add(result)
            session.flush()
            self.photo_repository.upload_photo(
                INPAINTER_GEN_BUCKET, filename,
                generated.filetype, generated.image,
            )
            logging.warning('gotten link %r', result.image_link)

            session.commit()


@celery_app.task(base=InpaintPhoto, bind=True, name='inpaint_photo')
def inpaint_photo(self: InpaintPhoto, generation_request_id: uuid.UUID):
    return self.execute(generation_request_id)
