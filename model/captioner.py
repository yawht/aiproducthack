from transformers import pipeline
import logging

PROMPT = "The main subject of this picture is a"

class Captioner:
    def __init__(self):
        logging.basicConfig(level=logging.INFO)
        logging.info("Initializing captioner...")

        self.captioner = pipeline(
            "image-to-text",
            model="Salesforce/blip-image-captioning-base",
            prompt=PROMPT
        )


    def derive_caption(self, image):
        result = self.captioner(image, max_new_tokens=20)
        raw_caption = result[0]["generated_text"]
        caption = raw_caption.lower().replace(PROMPT.lower(), "").strip()
        return caption
