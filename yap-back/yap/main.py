from fastapi import FastAPI
from yap.router.generation import generation_router
from yap.router.prompt import prompt_router
from yap.settings import settings

import uvicorn

app = FastAPI()


@app.get("/health")
def health():
    return "OK"


app.include_router(generation_router)
app.include_router(prompt_router)


def main():
    uvicorn.run(app, host=settings.app_host, port=int(settings.app_port), log_level="info")


if __name__ == "__main__":
    main()
