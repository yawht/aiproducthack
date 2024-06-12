import requests
import torch
import logging
import numpy as np
import io

from typing import Optional
from dataclasses import dataclass
from PIL import Image, ImageFilter
from scipy.ndimage import binary_dilation
from random import randint

from yap.ml_processors.image_utils import ensure_resolution, crop_centered
from yap.ml_processors.upscaler import Upscaler
from yap.ml_processors.segmenter import Segmenter
from yap.ml_processors.depth_estimator import DepthEstimator
from yap.ml_processors.controlnet_sdxl import ControlNet



TARGET_RESOLUTION_MEGAPIXELS = 1.0

DEPTH_MAP_FEATURE_THRESHOLD: int = 128
DEPTH_MAP_DILATION_ITERATIONS: int = 10
DEPTH_MAP_BLUR_RADIUS: int = 10
NUM_INFERENCE_STEPS: int = 30

POSITIVE_PROMPT_SUFFIX = 'commercial product photography, 24mm lens f/8'
NEGATIVE_PROMPT_SUFFIX = 'cartoon, drawing, anime, semi-realistic, illustration, painting, art, text, greyscale, (black and white), lens flare, watermark, cropped, out of frame, worst quality, low quality, jpeg artifacts, ugly, duplicate, morbid, mutilated, extra fingers, mutated hands, poorly drawn hands, poorly drawn face, mutation, deformed, dehydrated, bad anatomy, bad proportions, extra limbs, cloned face, disfigured, gross proportions, malformed limbs, missing arms, missing legs, extra arms, extra legs, fused fingers, too many fingers, long neck, floating, levitating'



@dataclass
class InpainterInput:
    image_link: str
    description: str
    positive_prompt: Optional[str]
    negative_prompt: str


@dataclass
class InpainterOutput:
    image: bytes
    filetype: str


class InpaintProcessor:
    """
    Этот код поедет к мльщикам, в другой пакет
    """

    def __init__(self, device: str = "cuda"):
        self._upscaler = Upscaler(device=device)
        self._segmenter = Segmenter(device=device)
        self._depth_estimator = DepthEstimator(device=device)

        self._controlnet = ControlNet(device=device)

    def _input_preprocess(
        self,
        image: Image,
    ) -> (Image, Image):
        logging.info("Original image size: %r", image.size)
        resized = ensure_resolution(image, self._upscaler, megapixels=TARGET_RESOLUTION_MEGAPIXELS)
        logging.info(
            "Ensuring resolution (%r MP), resized size %r",
            TARGET_RESOLUTION_MEGAPIXELS, resized.size,
        )

        torch.cuda.empty_cache()
        logging.info("Segmentation")
        [cropped, crop_mask] = self._segmenter.segment(resized)

        torch.cuda.empty_cache()
        logging.info("Depth mapping")
        depth_map = self._depth_estimator.get_depth_map(resized)

        torch.cuda.empty_cache()
        logging.info("Feathering the depth map")
        # Convert crop mask to grayscale and to numpy array
        crop_mask_np = np.array(crop_mask.convert("L"))

        # Convert to binary and dilate (grow) the edges
        # adjust threshold as needed
        crop_mask_binary = crop_mask_np > DEPTH_MAP_FEATURE_THRESHOLD
        # adjust iterations as needed
        dilated_mask = binary_dilation(
            crop_mask_binary, iterations=DEPTH_MAP_DILATION_ITERATIONS
        )

        # Convert back to PIL Image
        dilated_mask = Image.fromarray((dilated_mask * 255).astype(np.uint8))

        # Apply Gaussian blur and normalize
        dilated_mask_blurred = dilated_mask.filter(
            ImageFilter.GaussianBlur(radius=DEPTH_MAP_BLUR_RADIUS)
        )
        dilated_mask_blurred_np = np.array(dilated_mask_blurred) / 255.0

        # Normalize depth map, apply blurred, dilated mask, and scale back
        depth_map_np = np.array(depth_map.convert('L')) / 255.0
        masked_depth_map_np = depth_map_np * dilated_mask_blurred_np
        masked_depth_map_np = (masked_depth_map_np * 255).astype(np.uint8)

        # Convert back to PIL Image
        masked_depth_map = Image.fromarray(masked_depth_map_np).convert('RGB')

        return cropped, masked_depth_map

    def process(self, inp: InpainterInput) -> InpainterOutput:
        resp = requests.get(inp.image_link)

        image = Image.open(io.BytesIO(resp.content))
        cropped, ready_image = self._input_preprocess(image)

        final_positive_prompt = (
            f'{inp.description}, {inp.positive_prompt}, {POSITIVE_PROMPT_SUFFIX}'
        )
        logging.info('Final positive prompt: %s', final_positive_prompt)

        final_negative_prompt = f'{inp.negative_prompt}, {NEGATIVE_PROMPT_SUFFIX}'
        logging.info('Final negative prompt %s', final_negative_prompt)

        torch.cuda.empty_cache()
        logging.info("Generating")
        generated_images = self._controlnet.generate(
            positive_prompt=final_positive_prompt,
            negative_prompt=final_negative_prompt,
            image=[ready_image],
            num_inference_steps=NUM_INFERENCE_STEPS,
            seed=randint(0, 10000),
        )

        torch.cuda.empty_cache()
        logging.info("Compositing")
        composited_image = Image.alpha_composite(
            generated_images[0].convert("RGBA"),
            crop_centered(cropped, generated_images[0].size),
        )
        logging.info("Image inpainted")
        return InpainterOutput(composited_image.tobytes(), 'jpeg')

