import json
import os
from flask import Flask, render_template, request, Response, stream_with_context

import config
from segmenter import segment_text
from prompt_engineer import extract_story_bible, build_prompt
from image_generator import generate_image

app = Flask(__name__)
os.makedirs(config.OUTPUT_DIR, exist_ok=True)


@app.route("/")
def index():
    return render_template(
        "index.html",
        styles=list(config.STYLES.keys()),
        default_style=config.DEFAULT_STYLE,
        llm_providers=config.LLM_PROVIDERS,
        default_llm=config.DEFAULT_LLM,
        image_backends=config.IMAGE_BACKENDS,
        default_img_backend=config.DEFAULT_IMAGE_BACKEND,
    )


@app.route("/generate")
def generate():
    """
    SSE endpoint. Streams JSON events to the client as each panel is built.

    Query params:
        text        — the narrative text
        style       — visual style key
        llm         — LLM provider key
        img_backend — image generation backend
    """
    text        = request.args.get("text", "").strip()
    style       = request.args.get("style", config.DEFAULT_STYLE)
    llm         = request.args.get("llm", config.DEFAULT_LLM)
    img_backend = request.args.get("img_backend", config.DEFAULT_IMAGE_BACKEND)

    if not text:
        def error_stream():
            yield _sse({"type": "error", "message": "No text provided."})
        return Response(stream_with_context(error_stream()), mimetype="text/event-stream")

    def event_stream():
        try:
            # ── Step 1: Segment ───────────────────────────────────────────────
            yield _sse({"type": "status", "message": "Segmenting narrative…"})
            segments = segment_text(text)
            total = len(segments)

            # ── Step 2: Extract story bible ONCE for the full narrative ───────
            yield _sse({"type": "status", "message": f"Analysing narrative with {llm} — building visual bible…"})
            bible = extract_story_bible(text, llm)

            # Stream the bible to the UI so users can see what was extracted
            yield _sse({
                "type":  "bible",
                "data":  bible,
                "total": total,
            })

            # ── Step 3: Per-panel: refine prompt → generate image ─────────────
            for seg in segments:
                idx      = seg["index"]
                sentence = seg["text"]

                yield _sse({"type": "status", "message": f"Panel {idx}/{total}: crafting prompt…"})
                prompt = build_prompt(sentence, style, llm, bible=bible)

                yield _sse({"type": "status", "message": f"Panel {idx}/{total}: generating image…"})
                image_url = generate_image(prompt, idx, img_backend)

                yield _sse({
                    "type":      "panel",
                    "index":     idx,
                    "total":     total,
                    "sentence":  sentence,
                    "prompt":    prompt,
                    "image_url": image_url,
                })

            yield _sse({"type": "done", "message": "Storyboard complete!"})

        except Exception as e:
            yield _sse({"type": "error", "message": str(e)})

    return Response(
        stream_with_context(event_stream()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


def _sse(data: dict) -> str:
    return f"data: {json.dumps(data)}\n\n"


if __name__ == "__main__":
    app.run(debug=True, threaded=True)