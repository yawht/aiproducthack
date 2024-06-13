import math
from PIL import Image
import logging
from upscaler import Upscaler

UPSCALE_PIXEL_THRESHOLD = 1
DOWNSCALE_PIXEL_THRESHOLD = 1


def maybe_upscale(original, upscaler_inst: Upscaler, megapixels=1.0):
    original_width, original_height = original.size
    original_pixels = original_width * original_height
    target_pixels = megapixels * 1024 * 1024

    if (original_pixels < target_pixels):
        scale_by = math.sqrt(target_pixels / original_pixels)
        target_width = original_width * scale_by
        target_height = original_height * scale_by

        if (target_width - original_width >= 1 or target_height - original_height >= UPSCALE_PIXEL_THRESHOLD):
            logging.info("Upscaling...")

            upscaled = upscaler_inst.upscale(original)

            logging.info(f"Upscaled size: {upscaled.size}")

            return upscaled

    logging.info("Not upscaling")
    return original


def maybe_downscale(original, megapixels=1.0):
    original_width, original_height = original.size
    original_pixels = original_width * original_height
    target_pixels = megapixels * 1024 * 1024

    if (original_pixels > target_pixels):
        scale_by = math.sqrt(target_pixels / original_pixels)
        target_width = original_width * scale_by
        target_height = original_height * scale_by

        if (original_width - target_width >= 1 or original_height - target_height >= DOWNSCALE_PIXEL_THRESHOLD):
            logging.info("Downscaling...")

            target_width = round(target_width)
            target_height = round(target_height)

            downscaled = original.resize(
                (target_width, target_height), Image.LANCZOS)

            logging.info(f"Downscaled size: {downscaled.size}")

            return downscaled

    logging.info("Not downscaling")
    return original


def ensure_resolution(original, upscaler_inst: Upscaler, megapixels=1.0):
    return maybe_downscale(maybe_upscale(original, upscaler_inst, megapixels), megapixels)


def crop_centered(image, target_size):
    original_width, original_height = image.size
    target_width, target_height = target_size

    left = (original_width - target_width) / 2
    top = (original_height - target_height) / 2
    right = (original_width + target_width) / 2
    bottom = (original_height + target_height) / 2

    return image.crop((left, top, right, bottom))
