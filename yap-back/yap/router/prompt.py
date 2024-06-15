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

Product: Шезлонг 100х63х97 см сталь черный/серый
Prompt: located in the courtyard of the house, on the grass, next to the table, daytime weather, the sun is shining

Product: {req.description}
Prompt: 
"""
    generated: GenerateResponse = ollama_client.generate(
        model=settings.ollama_model,
        system=settings.ollama_system,
        prompt=prompt,
        stream=False,
        options={
            "num_predict": 128,
            "seed": 0,
            "temperature": 0.8,
        }
    )
    return GeneratePromptResponse(prompt=generated["response"]) # God why they cant use dataclasses
