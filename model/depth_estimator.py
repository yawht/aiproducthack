import torch
import numpy as np
from PIL import Image
from transformers import DPTFeatureExtractor, DPTForDepthEstimation
import logging

depth_estimator = None
feature_extractor = None


class DepthEstimator:
    def __init__(
        self,
        device: str = "cuda",
        depth_estimator: str = "Intel/dpt-hybrid-midas",
        feature_extractor: str = "Intel/dpt-hybrid-midas",
    ):
        logging.basicConfig(level=logging.INFO)
        logging.info("Initializing depth estimator...")

        if device == "cuda" and not torch.cuda.is_available():
            logging.warn("CUDA is not available, using CPU...")
            device = "cpu"
        self.device = device

        self.depth_estimator = DPTForDepthEstimation.from_pretrained(
            depth_estimator
        ).to(self.device)
        self.feature_extractor = DPTFeatureExtractor.from_pretrained(
            feature_extractor
        )


    def get_depth_map(self, image):
        original_size = image.size

        image = self.feature_extractor(images=image, return_tensors="pt").pixel_values.to(self.device)

        with torch.no_grad(), torch.autocast(self.device):
            depth_map = self.depth_estimator(image).predicted_depth

        depth_map = torch.nn.functional.interpolate(
            depth_map.unsqueeze(1),
            size=original_size[::-1],
            mode="bicubic",
            align_corners=False,
        )

        depth_min = torch.amin(depth_map, dim=[1, 2, 3], keepdim=True)
        depth_max = torch.amax(depth_map, dim=[1, 2, 3], keepdim=True)
        depth_map = (depth_map - depth_min) / (depth_max - depth_min)
        image = torch.cat([depth_map] * 3, dim=1)

        image = image.permute(0, 2, 3, 1).cpu().numpy()[0]
        image = Image.fromarray((image * 255.0).clip(0, 255).astype(np.uint8))

        return image
