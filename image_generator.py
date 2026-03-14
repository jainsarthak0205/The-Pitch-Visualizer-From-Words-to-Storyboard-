import os
import uuid
import requests
import base64
from PIL import Image
from io import BytesIO

import config

# ── Local SD Pipeline singleton ───────────────────────────────────────────────
_pipeline = None


def _get_local_pipeline():
    global _pipeline
    if _pipeline is not None:
        return _pipeline

    import torch
    from diffusers import StableDiffusionPipeline

    print(f"[image_generator] Loading local model: {config.SD_MODEL_ID}")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    dtype = torch.float16 if device == "cuda" else torch.float32

    pipe = StableDiffusionPipeline.from_pretrained(
        config.SD_MODEL_ID,
        torch_dtype=dtype,
        safety_checker=None,
        requires_safety_checker=False,
    )
    pipe = pipe.to(device)

    if device == "cuda":
        pipe.enable_attention_slicing()
    else:
        print("[image_generator] Running on CPU — generation will be slow.")

    _pipeline = pipe
    print(f"[image_generator] Model loaded on {device.upper()}.")
    return _pipeline


# ── Local Stable Diffusion ────────────────────────────────────────────────────
def _generate_local(prompt: str, panel_index: int) -> str:
    import torch

    pipe = _get_local_pipeline()

    negative_prompt = (
        "blurry, low quality, distorted, watermark, text, ugly, duplicate, "
        "morbid, mutilated, extra fingers, poorly drawn hands, poorly drawn face"
    )

    with torch.inference_mode():
        result = pipe(
            prompt=prompt,
            negative_prompt=negative_prompt,
            width=config.IMAGE_WIDTH,
            height=config.IMAGE_HEIGHT,
            num_inference_steps=config.INFERENCE_STEPS,
            guidance_scale=config.GUIDANCE_SCALE,
        )

    return _save_image(result.images[0], panel_index)


# ── Stability AI API ──────────────────────────────────────────────────────────
def _generate_stability(prompt: str, panel_index: int) -> str:
    if not config.STABILITY_API_KEY:
        raise ValueError("STABILITY_API_KEY is not set. Add it to your environment variables.")

    url = f"https://api.stability.ai/v1/generation/{config.STABILITY_ENGINE}/text-to-image"

    headers = {
        "Authorization": f"Bearer {config.STABILITY_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    body = {
        "text_prompts": [
            {"text": prompt, "weight": 1.0},
            {"text": "blurry, low quality, distorted, watermark, ugly", "weight": -1.0},
        ],
        "cfg_scale": config.GUIDANCE_SCALE,
        "width": config.STABILITY_IMAGE_WIDTH,
        "height": config.STABILITY_IMAGE_HEIGHT,
        "samples": 1,
        "steps": config.INFERENCE_STEPS,
    }

    response = requests.post(url, headers=headers, json=body)
    response.raise_for_status()

    image_data = response.json()["artifacts"][0]["base64"]
    image = Image.open(BytesIO(base64.b64decode(image_data)))
    return _save_image(image, panel_index)


# ── DALL-E 3 API ──────────────────────────────────────────────────────────────
def _generate_dalle(prompt: str, panel_index: int) -> str:
    if not config.OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY is not set. Add it to your environment variables.")

    from openai import OpenAI
    client = OpenAI(api_key=config.OPENAI_API_KEY)

    response = client.images.generate(
        model=config.DALLE_MODEL,
        prompt=prompt,
        size=config.DALLE_SIZE,
        quality=config.DALLE_QUALITY,
        n=1,
        response_format="b64_json",
    )

    image_data = response.data[0].b64_json
    image = Image.open(BytesIO(base64.b64decode(image_data)))
    return _save_image(image, panel_index)


# ── Shared helpers ────────────────────────────────────────────────────────────
def _save_image(image: Image.Image, panel_index: int) -> str:
    os.makedirs(config.OUTPUT_DIR, exist_ok=True)
    filename = f"panel_{panel_index}_{uuid.uuid4().hex[:8]}.png"
    filepath = os.path.join(config.OUTPUT_DIR, filename)
    image.save(filepath)
    return f"/static/outputs/{filename}"


# ── Public API ────────────────────────────────────────────────────────────────
def generate_image(prompt: str, panel_index: int, backend: str = None) -> str:
    """
    Generate a single image and save it to the output directory.

    Args:
        prompt:       Full image generation prompt.
        panel_index:  Used in filename for ordering.
        backend:      'local' | 'stability' | 'dalle'
                      Defaults to config.DEFAULT_IMAGE_BACKEND.

    Returns:
        Relative URL path, e.g. '/static/outputs/panel_1_abc.png'
    """
    backend = backend or config.DEFAULT_IMAGE_BACKEND

    print(f"[image_generator] Backend: {backend} | Panel {panel_index}")

    if backend == "local":
        return _generate_local(prompt, panel_index)
    elif backend == "stability":
        return _generate_stability(prompt, panel_index)
    elif backend == "dalle":
        return _generate_dalle(prompt, panel_index)
    else:
        raise ValueError(f"Unknown image backend: '{backend}'. Choose from: local, stability, dalle")