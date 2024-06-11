import torch
from diffusers import (
    StableDiffusionXLControlNetPipeline,
    ControlNetModel,
    AutoencoderKL,
    UniPCMultistepScheduler,
)
from __future__ import annotations
import cv2
from typing import Optional

import numpy as np
import PIL
from PIL.Image import Image as PIL_Image
import logging

class ControlNet:

    def __init__(
        self,
        controlnet_model_id: str = "diffusers/controlnet-canny-sdxl-1.0",
        vae_model_id: str = "madebyollin/sdxl-vae-fp16-fix",
        base_model_id: str = "stabilityai/stable-diffusion-xl-base-1.0",
        device: str = "cuda"
    ) -> None:

        if device == "cuda" and torch.cuda.is_available():
            self.dtype = torch.float16
        else:
            logging.warning("Using CPU for inference. This may be slow.")
            self.device = "cpu"
            self.dtype = torch.float32

        self.controlnet = ControlNetModel.from_pretrained(
            controlnet_model_id,
            use_safetensors=True,
            torch_dtype=self.dtype,
        )

        self.vae = AutoencoderKL.from_pretrained(
            vae_model_id,
            torch_dtype=self.dtype,
        )

        self.pipe = StableDiffusionXLControlNetPipeline.from_pretrained(
            base_model_id,
            controlnet=[self.controlnet],
            vae=self.vae,
            torch_dtype=self.dtype,
            variant="fp16",
            use_safetensors=True,
        ).to(self.device)

        self.pipe.enable_model_cpu_offload()
        # speed up diffusion process with faster scheduler and memory optimization
        self.pipe.scheduler = UniPCMultistepScheduler.from_config(self.pipe.scheduler.config)
        # remove following line if xformers is not installed
        self.pipe.enable_xformers_memory_efficient_attention()

    def generate(
        self,
        image: PIL_Image,
        positive_prompt: str,
        negative_prompt: Optional[str] = None,
        seed: Optional[int] = 42,
        controlnet_conditioning_scale: Optional[float] = 0.65,
        num_inference_steps: Optional[int] = 50,
        guidance_scale: Optional[float] = 10.0,
    ) -> PIL_Image:

        if controlnet_conditioning_scale is None:
            controlnet_conditioning_scale = 1.0

        if num_inference_steps is None:
            num_inference_steps = 50

        if guidance_scale is None:
            guidance_scale = 5.0

        arr = np.array(image)
        arr = cv2.Canny(arr, 100, 200)
        arr = arr[:, :, None]
        arr = np.concatenate([arr, arr, arr], axis=2)
        image = PIL.Image.fromarray(arr)
        generator = torch.manual_seed(seed)

        return self.pipe(
            prompt=positive_prompt,
            image=image,
            negative_prompt=negative_prompt,
            num_images_per_prompt=1,
            controlnet_conditioning_scale=controlnet_conditioning_scale,
            num_inference_steps=num_inference_steps,
            guidance_scale=guidance_scale,
            generator=generator,
        ).to_tuple()[0][0]

