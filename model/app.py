import os

import gradio as gr

from background_replacer import BackgroundReplacer

developer_mode = os.getenv("DEV_MODE", False)

DEFAULT_POSITIVE_PROMPT = """
located in a cozy outdoor kitchen area, near a wooden deck, evening time, 
warm lighting from lanterns and string lights, surrounded by lush greenery 
and a few potted plants, BBQ atmosphere
"""
DEFAULT_NEGATIVE_PROMPT = """
curved lines, ornate, baroque, abstract, grunge, logo, text,word,cropped,
low quality,normal quality,username,watermark,signature,blurry,soft,soft 
line,sketch,ugly,logo,pixelated,lowres"
"""
INTRO = "AI Product Hackaton"

MORE_INFO = "Weee ^^"

replacer = BackgroundReplacer(device="cuda")


def generate(
    image,
    description,
    positive_prompt,
    negative_prompt,
    seed,
    depth_map_feather_threshold,
    depth_map_dilation_iterations,
    depth_map_blur_radius,
    progress=gr.Progress(track_tqdm=True),
):
    if image is None:
        return [None, None, None, None]

    return replacer.replace_background(
        image,
        description,
        positive_prompt,
        negative_prompt,
        seed=seed,
        depth_map_feather_threshold=depth_map_feather_threshold,
        depth_map_dilation_iterations=depth_map_dilation_iterations,
        depth_map_blur_radius=depth_map_blur_radius
    )


custom_css = """
    #image-upload {
        flex-grow: 1;
    }
    #params .tabs {
        display: flex;
        flex-direction: column;
        flex-grow: 1;
    }
    #params .tabitem[style="display: block;"] {
        flex-grow: 1;
        display: flex !important;
    }
    #params .gap {
        flex-grow: 1;
    }
    #params .form {
        flex-grow: 1 !important;
    }
    #params .form > :last-child{
        flex-grow: 1;
    }
    .md ol, .md ul {
        margin-left: 1rem;
    }
    .md img {
        margin-bottom: 1rem;
    }
"""

with gr.Blocks(css=custom_css) as iface:
    gr.Markdown(INTRO)

    with gr.Row():
        with gr.Column():
            image_upload = gr.Image(
                label="Product image", type="pil", elem_id="image-upload"
            )
        with gr.Column(elem_id="params"):
            with gr.Tab("Prompts"):
                description = gr.Textbox(label="Description", lines=3, value="")
                positive_prompt = gr.Textbox(
                    label="Positive Prompt: describe what you'd like to see",
                    lines=3,
                    value=DEFAULT_POSITIVE_PROMPT,
                )
                negative_prompt = gr.Textbox(
                    label="Negative Prompt: describe what you want to avoid",
                    lines=3,
                    value=DEFAULT_NEGATIVE_PROMPT,
                )
            if developer_mode:
                with gr.Tab("Options"):
                    seed = gr.Number(
                        label="Seed",
                        precision=0,
                        value=0,
                        elem_id="seed",
                        visible=developer_mode,
                    )
                    depth_map_feather_threshold = gr.Slider(
                        label="Depth map feather threshold",
                        value=128,
                        minimum=0,
                        maximum=255,
                        visible=developer_mode,
                    )
                    depth_map_dilation_iterations = gr.Number(
                        label="Depth map dilation iterations",
                        precision=0,
                        value=10,
                        minimum=0,
                        visible=developer_mode,
                    )
                    depth_map_blur_radius = gr.Number(
                        label="Depth map blur radius",
                        precision=0,
                        value=10,
                        minimum=0,
                        visible=developer_mode,
                    )
            else:
                seed = gr.Number(value=-1, visible=False)
                depth_map_feather_threshold = gr.Slider(value=128, visible=False)
                depth_map_dilation_iterations = gr.Number(
                    precision=0, value=10, visible=False
                )
                depth_map_blur_radius = gr.Number(precision=0, value=10, visible=False)

    gen_button = gr.Button(value="Generate!", variant="primary")

    with gr.Tab("Results"):
        results = gr.Gallery(show_label=False, object_fit="contain", columns=4)

    gr.Markdown(MORE_INFO)

    gen_button.click(
        fn=generate,
        inputs=[
            image_upload,
            description,
            positive_prompt,
            negative_prompt,
            seed,
            depth_map_feather_threshold,
            depth_map_dilation_iterations,
            depth_map_blur_radius,
        ],
        outputs=[results],
    )

iface.queue(api_open=False).launch(show_api=False)
