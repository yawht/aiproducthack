FROM bentoml/model-server:0.13.2-py38-gpu

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

WORKDIR /bento

COPY . .

ENV CONTROLNET_MODEL_ID "diffusers/controlnet-depth-sdxl-1.0"
ENV VAE_MODEL_ID "madebyollin/sdxl-vae-fp16-fix"
ENV BASE_MODEL_ID "stabilityai/stable-diffusion-xl-base-1.0"

RUN huggingface-cli download $CONTROLNET_MODEL_ID
RUN huggingface-cli download $VAE_MODEL_ID
RUN huggingface-cli download $BASE_MODEL_ID

ENTRYPOINT ["bentoml", "serve", "."]
