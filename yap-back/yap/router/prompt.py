from ollama import Client, GenerateResponse
from fastapi import APIRouter, Depends
from yap.router.api import GeneratePromptRequest, GeneratePromptResponse
from yap.dependencies import get_ollama_client
from yap.settings import settings


prompt_router = APIRouter()


@prompt_router.post("/api/prompt")
def generate_prompt(
    req: GeneratePromptRequest, ollama_client: Client = Depends(get_ollama_client)
) -> GeneratePromptResponse:
    prompt = f"""
You have been provided with a description of a product for the garden. It is necessary to come up with a prompt in English for stable diffusion in order to create a logical background for this object. The resulting photo must be commercial and promotional. You can write about lighting and objects nearby.
Product: {req.description}
"""
    generated: GenerateResponse = ollama_client.generate(
        model="suzume-llama-3-8B-multilingual-gguf_q8:latest",
        system=settings.ollama_system,
        prompt=prompt,
        stream=False,
    )
    return GeneratePromptResponse(prompt=generated.response)
