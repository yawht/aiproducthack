import warnings

warnings.filterwarnings("ignore", category=FutureWarning)  # nopep8
warnings.filterwarnings("ignore", category=UserWarning)  # nopep8
import os
import math
from tqdm import tqdm
import torch
from PIL import Image, ImageFilter
from scipy.ndimage import binary_dilation
import numpy as np
import PIL

from upscaler import Upscaler
from segmenter import Segmenter
from depth_estimator import DepthEstimator
from controlnet_sdxl import ControlNet
from image_utils import ensure_resolution, crop_centered
import logging
from typing import Tuple


class BackgroundReplacer:
    def __init__(self, device: str = "cuda"):
        self.developer_mode = os.getenv("DEV_MODE", False)

        self.upscaler = Upscaler(device=device)
        self.segmenter = Segmenter(device=device)
        self.depth_estimator = DepthEstimator(device=device)
        self.controlnet = ControlNet(device=device)

        torch.cuda.empty_cache()

        self.positive_prompt_suffix = "commercial product photography, 24mm lens f/8"
        self.negative_prompt_suffix = "cartoon, drawing, anime, semi-realistic, illustration, painting, art, text, greyscale, (black and white), lens flare, watermark, cropped, out of frame, worst quality, low quality, jpeg artifacts, ugly, duplicate, morbid, mutilated, extra fingers, mutated hands, poorly drawn hands, poorly drawn face, mutation, deformed, dehydrated, bad anatomy, bad proportions, extra limbs, cloned face, disfigured, gross proportions, malformed limbs, missing arms, missing legs, extra arms, extra legs, fused fingers, too many fingers, long neck, floating, levitating"

        self.megapixels = 1.0

    def preprocess(
        self,
        image: PIL.Image,
        depth_map_feather_threshold: int,
        depth_map_dilation_iterations: int,
        depth_map_blur_radius: int,
    ) -> Tuple[PIL.Image, PIL.Image]:
        logging.info(f"Original size: {image.size}")

        logging.info(f"Ensuring resolution ({self.megapixels}MP)...")
        resized = ensure_resolution(image, self.upscaler, megapixels=self.megapixels)

        logging.info(f"Resized size: {resized.size}")

        torch.cuda.empty_cache()

        logging.info("Segmenting...")
        [cropped, crop_mask] = self.segmenter.segment(resized)

        torch.cuda.empty_cache()

        logging.info("Depth mapping...")
        depth_map = self.depth_estimator.get_depth_map(resized)

        torch.cuda.empty_cache()

        logging.info("Feathering the depth map...")

        # Convert crop mask to grayscale and to numpy array
        crop_mask_np = np.array(crop_mask.convert("L"))

        # Convert to binary and dilate (grow) the edges
        # adjust threshold as needed
        crop_mask_binary = crop_mask_np > depth_map_feather_threshold
        # adjust iterations as needed
        dilated_mask = binary_dilation(
            crop_mask_binary, iterations=depth_map_dilation_iterations
        )

        # Convert back to PIL Image
        dilated_mask = Image.fromarray((dilated_mask * 255).astype(np.uint8))

        # Apply Gaussian blur and normalize
        dilated_mask_blurred = dilated_mask.filter(
            ImageFilter.GaussianBlur(radius=depth_map_blur_radius)
        )
        dilated_mask_blurred_np = np.array(dilated_mask_blurred) / 255.0

        # Normalize depth map, apply blurred, dilated mask, and scale back
        depth_map_np = np.array(depth_map.convert("L")) / 255.0
        masked_depth_map_np = depth_map_np * dilated_mask_blurred_np
        masked_depth_map_np = (masked_depth_map_np * 255).astype(np.uint8)

        # Convert back to PIL Image
        masked_depth_map = Image.fromarray(masked_depth_map_np).convert("RGB")


        return cropped, masked_depth_map

    def replace_background(
        self,
        image: PIL.Image,
        description: str,
        positive_prompt: str,
        negative_prompt: str,
        seed: int = 0,
        num_inference_steps: int = 30,
        depth_map_feather_threshold: int = 128,
        depth_map_dilation_iterations: int = 10,
        depth_map_blur_radius: int = 10,
    ) -> PIL.Image:
        pbar = tqdm(total=3)
        
        cropped, ready_image = self.preprocess(
            image,
            depth_map_feather_threshold=depth_map_feather_threshold,
            depth_map_dilation_iterations=depth_map_dilation_iterations,
            depth_map_blur_radius=depth_map_blur_radius,
        )
        pbar.update(1)

        final_positive_prompt = (
            f"{description}, {positive_prompt}, {self.positive_prompt_suffix}"
        )
        final_negative_prompt = f"{negative_prompt}, {self.negative_prompt_suffix}"

        logging.info(f"Final positive prompt: {final_positive_prompt}")
        logging.info(f"Final negative prompt: {final_negative_prompt}")

        logging.info("Generating...")

        generated_images = self.controlnet.generate(
            positive_prompt=final_positive_prompt,
            negative_prompt=final_negative_prompt,
            image=[ready_image],
            num_inference_steps=num_inference_steps,
            seed=seed,
        )
        torch.cuda.empty_cache()
        pbar.update(1)

        logging.info("Compositing...")

        composited_images = [
            Image.alpha_composite(
                generated_image.convert("RGBA"),
                crop_centered(cropped, generated_image.size),
            )
            for generated_image in generated_images
        ]
        pbar.update(1)
        pbar.close()

        logging.info("Done!")

        return composited_images[0]
