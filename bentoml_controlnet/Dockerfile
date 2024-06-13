FROM nvidia/cuda:12.1.0-cudnn8-devel-ubuntu22.04

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-distutils \
    python3-pip \
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
