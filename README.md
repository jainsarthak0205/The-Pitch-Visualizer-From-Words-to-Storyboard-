# 🎬 The Pitch Visualizer

> **Transform narrative text into a cinematic, multi-panel visual storyboard — automatically, intelligently, and beautifully.**

---

## What Is This?

The Pitch Visualizer is a full-stack AI application that takes a block of narrative text — a sales pitch, a customer success story, or any short story — and converts it into a visually cohesive storyboard, one panel at a time, directly in your browser.

It does not just slap a sentence onto an image generator. It reads the *entire* story first, extracts a **Visual Bible** (shared anchors for setting, palette, characters, mood, and lighting), and then uses that bible to ensure every panel feels like it belongs to the same world. The result is a storyboard where panels feel directed, not randomly generated.

---

## Key Features

| Feature | Details |
|---|---|
| **Two-Phase Prompt Engineering** | LLM first builds a Visual Bible from the full narrative, then generates each panel prompt using those shared anchors |
| **Visual Bible extraction** | Extracts setting, color palette, subject description, mood, and lighting — shown live in the UI |
| **NLTK Narrative Segmentation** | Intelligent sentence tokenizer with two fallback strategies for edge cases |
| **3 LLM providers** | Google Gemini, OpenAI GPT-4o, Anthropic Claude — switchable via dropdown |
| **3 Image backends** | Local Stable Diffusion (default, free), Stability AI API, DALL-E 3 |
| **8 Visual styles** | Cinematic, Digital Art, Watercolor, Comic, Oil Painting, Pixel Art, Neon Noir, Anime |
| **Panel-by-panel streaming** | Server-Sent Events reveal each panel the moment it's ready — no waiting for all images |
| **Skeleton loading UI** | Placeholder cards appear while each image generates |
| **Prompt inspector** | Expand any panel to see the exact prompt fed to the image model |
| **GPU/CPU auto-detection** | Automatically uses CUDA if available, silently falls back to CPU |

---

## How It Works — Architecture

```
User Input (narrative text)
        │
        ▼
┌─────────────────┐
│   segmenter.py  │  NLTK sent_tokenize → list of sentences (≥3)
└────────┬────────┘
         │
         ▼
┌──────────────────────────────────────────┐
│         prompt_engineer.py               │
│                                          │
│  Phase 1 — extract_story_bible()         │
│  ┌──────────────────────────────────┐    │
│  │  Full narrative → LLM (once)     │    │
│  │  Returns: setting, palette,      │    │
│  │  subject, mood, lighting         │    │
│  └──────────────────────────────────┘    │
│                                          │
│  Phase 2 — build_prompt() × N panels    │
│  ┌──────────────────────────────────┐    │
│  │  Sentence + Visual Bible → LLM   │    │
│  │  Returns: rich SD-ready prompt   │    │
│  │  + style suffix appended         │    │
│  └──────────────────────────────────┘    │
└──────────────────┬───────────────────────┘
                   │
                   ▼
        ┌──────────────────┐
        │ image_generator  │  SD local / Stability AI / DALL-E 3
        └────────┬─────────┘
                 │
                 ▼
        Flask SSE stream → Browser (panel by panel)
```

---

## Project Structure

```
pitch_visualizer/
├── app.py                  # Flask app + SSE streaming endpoint
├── segmenter.py            # NLTK-based narrative segmentation
├── prompt_engineer.py      # Two-phase LLM prompt engineering
├── image_generator.py      # Multi-backend image generation
├── config.py               # Central config: styles, models, keys
├── templates/
│   └── index.html          # Dynamic storyboard UI (SSE + Visual Bible card)
├── static/
│   └── outputs/            # Generated images (auto-created)
├── requirements.txt
└── README.md
```

---

## Setup & Installation

### Step 1 — Clone the repository

```bash
git clone https://github.com/jainsarthak0205/The-Pitch-Visualizer-From-Words-to-Storyboard-.git
cd pitch_visualizer
```

### Step 2 — Create a virtual environment

```bash
python -m venv venv

# macOS / Linux
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### Step 3 — Install PyTorch (GPU users only)

If you have an NVIDIA GPU, install the CUDA-enabled version of PyTorch **before** the next step. This is what enables fast local image generation.

```bash
# Check your CUDA version first:
nvidia-smi   # look for "CUDA Version" in the top right

# CUDA 12.1+
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# CUDA 11.8
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

If you don't have a GPU, skip this step — it will fall back to CPU automatically.

### Step 4 — Install dependencies

```bash
pip install -r requirements.txt
```

### Step 5 — Set your API keys

You only need **one** LLM key — **Gemini is recommended** as it is completely free with no credit card required. Get a free key at [aistudio.google.com](https://aistudio.google.com) in under 2 minutes.

**macOS / Linux:**
```bash
export GEMINI_API_KEY="AIza..."

# Optional — only needed if you want to use these providers or image backends
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
export STABILITY_API_KEY="sk-..."
```

**Windows (Command Prompt):**
```cmd
set GEMINI_API_KEY=AIza...
set OPENAI_API_KEY=sk-...
```

**Windows (PowerShell):**
```powershell
$env:GEMINI_API_KEY="AIza..."
$env:OPENAI_API_KEY="sk-..."
```

### Step 6 — Run

```bash
python app.py
```

Open **http://127.0.0.1:5000** in your browser.

---

## First Run Notes

- **First launch:** Stable Diffusion (`runwayml/stable-diffusion-v1-5`, ~4 GB) downloads automatically from HuggingFace and is cached in `~/.cache/huggingface/`. Subsequent runs load instantly from cache.
- **GPU:** ~10–30 seconds per image panel.
- **CPU:** ~3–8 minutes per panel. For faster testing, reduce `INFERENCE_STEPS` to `15` in `config.py`.
- To verify your GPU is detected, run:
  ```python
  import torch
  print(torch.cuda.is_available())      # True = GPU active
  print(torch.cuda.get_device_name(0))  # e.g. NVIDIA GeForce RTX 3080
  ```

---

## Usage Guide

1. Paste a narrative of **3–5 sentences** into the text area.
2. Choose an **Image Backend** (Local SD is default and free).
3. Pick a **Visual Style** (Cinematic, Anime, Watercolor, etc.).
4. Select a **Prompt LLM** (Gemini recommended).
5. Click **Generate Storyboard** or press `Ctrl+Enter`.

The app will:
- Segment your text into scenes
- Extract a **Visual Bible** (displayed as a card in the UI)
- Stream each panel as it finishes generating

**Example narrative to try:**

> *A small bakery in Lyon was struggling to survive after the pandemic forced them to close their doors. They partnered with us to launch a custom online ordering system and a social media presence from scratch. Within six months, their monthly revenue had doubled and they built a loyal customer base of over 2,000 people. Today they are opening a second location, funded entirely by that growth.*

---

## Configuration Reference (`config.py`)

| Parameter | Default | Description |
|---|---|---|
| `SD_MODEL_ID` | `runwayml/stable-diffusion-v1-5` | Any HuggingFace-compatible SD model |
| `INFERENCE_STEPS` | `30` | Image quality vs speed (15 = fast test, 50 = high quality) |
| `GUIDANCE_SCALE` | `7.5` | How strictly the model follows the prompt (5–15) |
| `IMAGE_WIDTH/HEIGHT` | `512` | Output resolution for local SD |
| `DEFAULT_STYLE` | `cinematic` | Pre-selected style on page load |
| `DEFAULT_LLM` | `gemini` | Pre-selected LLM on page load |
| `DEFAULT_IMAGE_BACKEND` | `local` | Pre-selected image backend |

---

## Design Choices & Methodology

### Narrative Segmentation
NLTK's `sent_tokenize` is the primary approach, leveraging a pre-trained Punkt tokenizer that understands abbreviations, punctuation edge cases, and sentence boundaries. Two fallback strategies handle unusual inputs:
1. **Newline split** — for bullet-point or line-break delimited input
2. **Word-chunk split** — guarantees at least 3 segments even for single-sentence inputs

Short fragments under 5 words are filtered out to avoid producing near-empty prompts.

### Prompt Engineering — Two-Phase Architecture

The central design insight of this project is that **visual consistency requires shared context**, and shared context requires reading the whole story before generating any single panel.

Most naive implementations send each sentence directly to an image generator. This produces panels that look like they belong to different stories — different characters, different lighting, different color palettes.

The solution is a two-phase approach:

**Phase 1 — Visual Bible Extraction**

Before any image is generated, the entire narrative is sent to the LLM with a system prompt that instructs it to return a structured JSON containing five visual anchors:

```json
{
  "setting":  "a narrow Parisian street at golden hour, warm cobblestone ambiance",
  "palette":  "warm amber, soft gold, terracotta, deep espresso brown",
  "subject":  "a middle-aged French woman in a flour-dusted white apron",
  "mood":     "resilient and hopeful",
  "lighting": "warm golden hour sunlight streaming through a bakery window"
}
```

These anchors are the *invariants* of the storyboard — elements that must remain constant across all panels to create visual cohesion.

**Phase 2 — Context-Anchored Panel Prompts**

Each sentence is then sent to the LLM individually, but this time the Visual Bible is injected as context alongside a detailed cinematographer-style system prompt. The LLM is explicitly instructed to:
- Depict the specific scene in the sentence
- Maintain the established subject appearance, setting, and lighting
- Specify a camera angle or composition
- Write in language appropriate to the chosen visual style

The resulting prompt is then suffixed with style-specific SD keywords (e.g. `anamorphic lens, film grain, color graded` for cinematic style) that further anchor the visual output.

**Why this works:** The LLM functions as both a story analyst and a cinematographer. Rather than generating a generic image of "a bakery", it generates "a close-up of a flour-dusted middle-aged French woman looking relieved, warm golden light through a bakery window, muted amber tones" — a description that is both scene-specific and visually consistent with every other panel.

### Style System
Each of the 8 visual styles has two components:
- `context` — natural language description given to the LLM, allowing it to craft scene descriptions that use the vocabulary of that style (e.g. "Think Rembrandt: chiaroscuro lighting, rich deep colours")
- `suffix` — SD-tuned keywords appended to the final prompt, targeting specific rendering behaviours in Stable Diffusion

### Streaming UI (SSE)
The `/generate` Flask endpoint is a Server-Sent Events generator. Rather than waiting for all images to complete, it yields JSON events progressively:
- `status` — updates the status bar with current step
- `bible` — fires once after Phase 1, populating the Visual Bible card
- `panel` — fires once per completed panel, triggering the slide-in animation
- `done` / `error` — terminal events

This architecture means the user sees value immediately — the Visual Bible appears in seconds, and panels stream in one by one rather than all at once after a long wait.

### Image Generation Backends
Three backends are supported with a clean routing architecture in `image_generator.py`:
- **Local (Stable Diffusion):** Uses HuggingFace Diffusers with auto GPU/CPU detection. The pipeline is a singleton — loaded once on first request, reused for all subsequent panels in a session.
- **Stability AI:** Calls the REST API with negative prompts for artefact suppression.
- **DALL-E 3:** Uses the OpenAI Python SDK, returning base64-encoded images decoded directly to disk.

---

## Deliverables Checklist

- [x] Text input — web textarea with example placeholder
- [x] Narrative segmentation — NLTK with 2 fallback strategies (≥3 scenes guaranteed)
- [x] Intelligent prompt engineering — two-phase LLM architecture with Visual Bible
- [x] Image generation — Stable Diffusion via HuggingFace Diffusers
- [x] Storyboard presentation — streaming HTML panels with captions
- [x] **Bonus:** Visual consistency — Visual Bible anchors all panels to shared setting, palette, subject, mood, lighting
- [x] **Bonus:** User-selectable styles — 8 styles, each with LLM context + SD suffix
- [x] **Bonus:** LLM-powered prompt refinement — OpenAI GPT-4o / Anthropic Claude / Google Gemini
- [x] **Bonus:** Dynamic panel-by-panel UI — SSE streaming with skeleton loaders and slide-in animations