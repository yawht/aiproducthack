FROM nvidia/cuda:12.1.0-cudnn8-devel-ubuntu22.04

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-distutils \
    python3-pip \
    ffmpeg \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

WORKDIR /bento

COPY . .

RUN mkdir -p saved_models git

RUN git clone https://github.com/xuebinqin/DIS git/xuebinqin/DIS

RUN python3 -c "from huggingface_hub import hf_hub_download; \
    hf_hub_download(repo_id='NimaBoscarino/IS-Net_DIS-general-use', \
    filename='isnet-general-use.pth', local_dir='saved_models')"

RUN rm -r git/xuebinqin/DIS/IS-Net/__pycache__

RUN mv git/xuebinqin/DIS/IS-Net/* .

ENTRYPOINT ["bentoml", "serve", "."]
