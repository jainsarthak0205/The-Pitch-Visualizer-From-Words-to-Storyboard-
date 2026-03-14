import os

# --- API Keys (set these as environment variables) ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
GEMINI_API_KEY = os.getenv("AIzaSyBYAPiKl5WsFI5jg1i-sLWBXMm11nlXFIQ", "")

# --- Stability AI (for API-based image generation) ---
STABILITY_API_KEY = os.getenv("STABILITY_API_KEY", "")

# --- Image Generation Backend ---
DEFAULT_IMAGE_BACKEND = "local"
IMAGE_BACKENDS = ["local", "stability", "dalle"]

# --- Local Stable Diffusion settings ---
SD_MODEL_ID = "runwayml/stable-diffusion-v1-5"
IMAGE_WIDTH = 512
IMAGE_HEIGHT = 512
INFERENCE_STEPS = 30
GUIDANCE_SCALE = 7.5

# --- Stability AI settings ---
STABILITY_ENGINE = "stable-diffusion-xl-1024-v1-0"
STABILITY_IMAGE_WIDTH = 1024
STABILITY_IMAGE_HEIGHT = 1024

# --- DALL-E settings ---
DALLE_MODEL = "dall-e-3"
DALLE_SIZE = "1024x1024"
DALLE_QUALITY = "standard"

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "static", "outputs")

# --- Visual Styles ---
# Each entry has two parts:
#   "suffix"  — appended to every panel prompt (SD-tuned keywords)
#   "context" — passed to the LLM so it crafts descriptions in the right visual language
STYLES = {
    "cinematic": {
        "suffix":  "cinematic photography, anamorphic lens, dramatic directional lighting, 8k RAW, shallow depth of field, color graded, film grain, ultra-realistic",
        "context": "cinematic film photography. Think Hollywood blockbuster: dramatic lighting, lens flares, shallow depth of field, muted warm/cool color grading, wide-angle establishing shots or tight close-ups.",
    },
    "digital_art": {
        "suffix":  "digital concept art, highly detailed illustration, ArtStation trending, professional matte painting, vibrant saturated colors, sharp edges, 4k",
        "context": "professional digital concept art. Think ArtStation portfolio: rich saturated colors, clean sharp lines, dramatic composition, detailed environments, hero lighting.",
    },
    "watercolor": {
        "suffix":  "watercolor painting, loose wet brushstrokes, soft bleeding edges, pastel washes, white paper texture, artistic, impressionistic, delicate",
        "context": "delicate watercolor painting. Think editorial illustration: soft bleeding edges, pastel tones, visible paper texture, loose expressive strokes, gentle mood.",
    },
    "comic": {
        "suffix":  "comic book art, bold ink outlines, flat cel colors, halftone dots, dynamic perspective, graphic novel, Marvel/DC style, high contrast",
        "context": "classic comic book art. Think Marvel or DC: bold black outlines, flat colors, dramatic perspective, action-ready poses, speech-bubble-ready compositions.",
    },
    "oil_painting": {
        "suffix":  "oil painting, thick impasto texture, old master technique, chiaroscuro lighting, rich jewel tones, museum quality, renaissance composition, detailed brushwork",
        "context": "classical oil painting in the old master tradition. Think Rembrandt or Caravaggio: dramatic chiaroscuro lighting, rich deep colours, visible brushwork, timeless compositional framing.",
    },
    "pixel_art": {
        "suffix":  "pixel art, 32-bit retro style, clean pixel edges, limited color palette, SNES-era aesthetic, isometric or side-scrolling perspective, detailed sprites",
        "context": "retro pixel art in the SNES/GBA era style. Think Chrono Trigger or Stardew Valley: limited color palette, clean pixels, charming character sprites, expressive minimalism.",
    },
    "neon_noir": {
        "suffix":  "neon noir, cyberpunk aesthetic, rain-slicked streets, neon light reflections, deep shadows, foggy atmosphere, blade runner palette, moody cinematic",
        "context": "neon noir cyberpunk aesthetic. Think Blade Runner or Cyberpunk 2077: rain-soaked streets, neon signs reflecting in puddles, deep shadows, fog, a palette of electric blues, magentas and golds.",
    },
    "anime": {
        "suffix":  "anime illustration, Studio Ghibli aesthetic, soft cel shading, expressive emotive characters, hand-painted backgrounds, vibrant natural lighting, 2D animation frame",
        "context": "Studio Ghibli-inspired anime illustration. Think Spirited Away or Princess Mononoke: lush painted backgrounds, soft cel-shaded characters, warm natural lighting, emotional expressiveness, painterly sky gradients.",
    },
}

DEFAULT_STYLE = "cinematic"

# --- LLM Prompt Engineering ---
LLM_PROVIDERS = ["gemini", "openai", "anthropic"]
DEFAULT_LLM = "gemini"

# ── Phase 1: Story Bible extraction ──────────────────────────────────────────
# Called ONCE with the full narrative to extract visual anchors shared across panels.
STORY_BIBLE_SYSTEM = """You are a visual development artist preparing a storyboard for a short narrative.
Your job is to read the full story and extract a VISUAL BIBLE — a set of consistent anchors
that every panel in the storyboard must share.

Return ONLY a compact JSON object with these exact keys (no markdown, no explanation):
{
  "setting": "one sentence describing the primary location and time of day",
  "palette": "3-5 dominant colors and overall tone, e.g. 'warm amber, dusty terracotta, deep indigo, golden hour'",
  "subject": "brief description of the main character or central subject that recurs across panels",
  "mood": "the emotional atmosphere, e.g. 'hopeful and determined' or 'tense and shadowy'",
  "lighting": "consistent lighting condition, e.g. 'soft diffused morning light' or 'harsh neon backlit'"
}"""

# ── Phase 2: Per-panel prompt generation ─────────────────────────────────────
# Called once per sentence, with story bible context injected.
PANEL_PROMPT_SYSTEM = """You are a cinematographer and storyboard artist writing image generation prompts.
You will receive:
  - A single sentence from a narrative (the scene to depict)
  - A visual bible with established anchors (setting, palette, subject, mood, lighting)
  - The target visual style

Your task: write ONE image generation prompt that:
1. Depicts the scene in the sentence faithfully
2. Maintains the established setting, palette, subject appearance, and lighting from the visual bible
3. Uses cinematic/artistic language appropriate to the style
4. Specifies camera angle or composition (e.g. wide shot, close-up, over-the-shoulder)
5. Is between 40-70 words

Return ONLY the prompt text. No preamble, no explanation, no quotes."""