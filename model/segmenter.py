# Based on https://github.com/xuebinqin/DIS/blob/main/Colab_Demo.ipynb
import os
from huggingface_hub import hf_hub_download

from PIL import Image
import numpy as np
import torch
from torch.autograd import Variable
from torchvision import transforms
import torch.nn.functional as F
import matplotlib.pyplot as plt
import logging
import torch.nn as nn
from typing import List, Tuple, Dict, Optional, Any

class GOSNormalize(object):
    '''
    Normalize the Image using torch.transforms
    '''

    def __init__(self, normalize, mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]):
        self.mean = mean
        self.std = std
        self.normalize = normalize

    def __call__(self, image):
        image = self.normalize(image, self.mean, self.std)
        return image
    
class Segmenter:
    def __init__(self, device: str = "cuda"):
        logging.basicConfig(level=logging.INFO)
        logging.info("Initializing segmenter...")

        if device == "cuda" and not torch.cuda.is_available():
            logging.warn("CUDA is not available, using CPU...")
            device = "cpu"
        self.device = device
        
        if not os.path.exists("saved_models"):
            os.mkdir("saved_models")
            os.mkdir("git")
            os.system(
                "git clone https://github.com/xuebinqin/DIS git/xuebinqin/DIS")
            hf_hub_download(repo_id="NimaBoscarino/IS-Net_DIS-general-use",
                            filename="isnet-general-use.pth", local_dir="saved_models")
            os.system("rm -r git/xuebinqin/DIS/IS-Net/__pycache__")
            os.system(
                "mv git/xuebinqin/DIS/IS-Net/* .")

        import models
        import data_loader_cache

        self.ISNetDIS = models.ISNetDIS
        self.normalize = data_loader_cache.normalize
        self.im_preprocess = data_loader_cache.im_preprocess

        # Set Parameters
        self.hypar = {}  # paramters for inferencing

        # load trained weights from this path
        self.hypar["model_path"] = "./saved_models"
        # name of the to-be-loaded weights
        self.hypar["restore_model"] = "isnet-general-use.pth"
        # indicate if activate intermediate feature supervision
        self.hypar["interm_sup"] = False

        # choose floating point accuracy --
        # indicates "half" or "full" accuracy of float number
        self.hypar["model_digit"] = "full"
        self.hypar["seed"] = 0

        # cached input spatial resolution, can be configured into different size
        self.hypar["cache_size"] = [1024, 1024]

        # data augmentation parameters ---
        # mdoel input spatial size, usually use the same value hypar["cache_size"], which means we don't further resize the images
        self.hypar["input_size"] = [1024, 1024]
        # random crop size from the input, it is usually set as smaller than hypar["cache_size"], e.g., [920,920] for data augmentation
        self.hypar["crop_size"] = [1024, 1024]

        self.hypar["model"] = self.ISNetDIS()

        # Build Model
        self.net = self.build_model()

        self.transform = transforms.Compose(
             [GOSNormalize(self.normalize, [0.5, 0.5, 0.5], [1.0, 1.0, 1.0])]
        )

    def load_image(self, im_pil: Image) -> Any:
        im = np.array(im_pil)
        im, im_shp = self.im_preprocess(im, self.hypar["cache_size"])
        im = torch.divide(im, 255.0)
        shape = torch.from_numpy(np.array(im_shp))
        # make a batch of image, shape
        return self.transform(im).unsqueeze(0), shape.unsqueeze(0)


    def build_model(self):
        net = self.hypar["model"]  # GOSNETINC(3,1)

        # convert to half precision
        if (self.hypar["model_digit"] == "half"):
            net.half()
            for layer in net.modules():
                if isinstance(layer, nn.BatchNorm2d):
                    layer.float()
        net.to(self.device)

        if (self.hypar["restore_model"] != ""):
            net.load_state_dict(torch.load(
                self.hypar["model_path"] + "/" + self.hypar["restore_model"], map_location=self.device))
            net.to(self.device)

        net.eval()
        return net


    def predict(self, inputs_val, shapes_val):
        '''
        Given an Image, predict the mask
        '''
        self.net.eval()

        if (self.hypar["model_digit"] == "full"):
            inputs_val = inputs_val.type(torch.FloatTensor)
        else:
            inputs_val = inputs_val.type(torch.HalfTensor)

        inputs_val_v = Variable(inputs_val, requires_grad=False).to(
            self.device)  # wrap inputs in Variable

        ds_val = self.net(inputs_val_v)[0]  # list of 6 results

        # B x 1 x H x W    # we want the first one which is the most accurate prediction
        pred_val = ds_val[0][0, :, :, :]

        # recover the prediction spatial size to the orignal image size
        pred_val = torch.squeeze(F.upsample(torch.unsqueeze(
            pred_val, 0), (shapes_val[0][0], shapes_val[0][1]), mode='bilinear'))

        ma = torch.max(pred_val)
        mi = torch.min(pred_val)
        pred_val = (pred_val-mi)/(ma-mi)  # max = 1

        if self.device == 'cuda':
            torch.cuda.empty_cache()
        # it is the mask we need
        return (pred_val.detach().cpu().numpy()*255).astype(np.uint8)


    def segment(self, image: Image):
        image_tensor, orig_size = self.load_image(image)
        mask = self.predict(image_tensor, orig_size, self.device)

        mask = Image.fromarray(mask).convert('L')
        im_rgb = image.convert("RGB")

        cropped = im_rgb.copy()
        cropped.putalpha(mask)

        return [cropped, mask]
