from fastapi import FastAPI
from datetime import datetime
from yap.api import Generation

import uvicorn
import uuid

app = FastAPI()


@app.get("/health")
async def health():
    return "OK"


@app.get("/api/generations")
async def generations() -> list[Generation]:
    return [
        Generation(
            uid=uuid.uuid4(),
            status="FINISHED",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            finished_at=datetime.now(),
            metadata={
                "model": "diffusion-imprinter",
                "source_image": "https://our.cdn.io/sources/uuid_ex",
                "result_image": "https://our.cdn.io/results/uuid_ex",
            },
        )
    ]


def main():
    uvicorn.run(app, port=8080, log_level="info")


if __name__ == "__main__":
    uvicorn.run(app, port=8080, log_level="info")
