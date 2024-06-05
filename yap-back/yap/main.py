from fastapi import FastAPI
from yap.router.generation import generation_router

import uvicorn

app = FastAPI()


@app.get("/health")
def health():
    return "OK"


app.include_router(generation_router)


def main():
    uvicorn.run(app, port=8080, log_level="info")


if __name__ == "__main__":
    uvicorn.run(app, port=8080, log_level="info")
