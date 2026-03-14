import json
import re
import config

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _extract_json(text: str) -> dict:
    """Safely parse JSON from an LLM response, stripping markdown fences."""
    text = re.sub(r"```(?:json)?", "", text).strip().strip("`")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Best-effort: return empty dict, fallback will handle it
        return {}


def _bible_to_text(bible: dict) -> str:
    """Convert a story bible dict into a compact string for prompt injection."""
    if not bible:
        return ""
    lines = []
    for key in ("setting", "palette", "subject", "mood", "lighting"):
        if bible.get(key):
            lines.append(f"{key.capitalize()}: {bible[key]}")
    return "\n".join(lines)


def _fallback_bible(full_text: str) -> dict:
    """Produce a minimal story bible without an LLM."""
    words = full_text.split()
    snippet = " ".join(words[:20])
    return {
        "setting": "a real-world contemporary environment",
        "palette": "natural tones, soft highlights",
        "subject": f"the central figure described in: {snippet}…",
        "mood": "engaging and purposeful",
        "lighting": "soft, natural directional light",
    }


def _fallback_panel(sentence: str, style: str, bible: dict) -> str:
    """Produce a reasonable panel prompt without an LLM."""
    style_ctx = config.STYLES.get(style, config.STYLES[config.DEFAULT_STYLE])
    ctx = style_ctx["context"] if isinstance(style_ctx, dict) else style_ctx
    setting  = bible.get("setting", "")
    lighting = bible.get("lighting", "")
    mood     = bible.get("mood", "")
    return (
        f"A scene depicting: {sentence}. "
        f"Setting: {setting}. {lighting}. {mood} atmosphere. "
        f"Rendered as {ctx}. Highly detailed, professional composition."
    )


# ─────────────────────────────────────────────────────────────────────────────
# LLM call wrappers — Phase 1 (Story Bible)
# ─────────────────────────────────────────────────────────────────────────────

def _bible_openai(full_text: str, api_key: str) -> dict:
    from openai import OpenAI
    client = OpenAI(api_key=api_key)
    resp = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": config.STORY_BIBLE_SYSTEM},
            {"role": "user",   "content": f"Narrative:\n{full_text}"},
        ],
        max_tokens=300,
        temperature=0.4,
        response_format={"type": "json_object"},
    )
    return _extract_json(resp.choices[0].message.content)


def _bible_anthropic(full_text: str, api_key: str) -> dict:
    import anthropic
    client = anthropic.Anthropic(api_key=api_key)
    msg = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=300,
        system=config.STORY_BIBLE_SYSTEM,
        messages=[{"role": "user", "content": f"Narrative:\n{full_text}"}],
    )
    return _extract_json(msg.content[0].text)


def _bible_gemini(full_text: str, api_key: str) -> dict:
    import google.generativeai as genai
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        system_instruction=config.STORY_BIBLE_SYSTEM,
    )
    resp = model.generate_content(f"Narrative:\n{full_text}")
    return _extract_json(resp.text)


# ─────────────────────────────────────────────────────────────────────────────
# LLM call wrappers — Phase 2 (Panel Prompt)
# ─────────────────────────────────────────────────────────────────────────────

def _panel_openai(sentence: str, style: str, bible_text: str, api_key: str) -> str:
    from openai import OpenAI
    client = OpenAI(api_key=api_key)
    user_msg = _build_panel_user_msg(sentence, style, bible_text)
    resp = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": config.PANEL_PROMPT_SYSTEM},
            {"role": "user",   "content": user_msg},
        ],
        max_tokens=200,
        temperature=0.75,
    )
    return resp.choices[0].message.content.strip()


def _panel_anthropic(sentence: str, style: str, bible_text: str, api_key: str) -> str:
    import anthropic
    client = anthropic.Anthropic(api_key=api_key)
    user_msg = _build_panel_user_msg(sentence, style, bible_text)
    msg = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=200,
        system=config.PANEL_PROMPT_SYSTEM,
        messages=[{"role": "user", "content": user_msg}],
    )
    return msg.content[0].text.strip()


def _panel_gemini(sentence: str, style: str, bible_text: str, api_key: str) -> str:
    import google.generativeai as genai
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        system_instruction=config.PANEL_PROMPT_SYSTEM,
    )
    user_msg = _build_panel_user_msg(sentence, style, bible_text)
    resp = model.generate_content(user_msg)
    return resp.text.strip()


def _build_panel_user_msg(sentence: str, style: str, bible_text: str) -> str:
    style_data = config.STYLES.get(style, config.STYLES[config.DEFAULT_STYLE])
    style_ctx  = style_data["context"] if isinstance(style_data, dict) else style_data
    return (
        f"Scene to depict:\n\"{sentence}\"\n\n"
        f"Visual Bible:\n{bible_text}\n\n"
        f"Target style: {style_ctx}\n\n"
        "Write the image generation prompt now."
    )


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def extract_story_bible(full_text: str, llm_provider: str) -> dict:
    """
    Phase 1 — called ONCE for the entire narrative.
    Returns a story bible dict with keys: setting, palette, subject, mood, lighting.
    Falls back gracefully if LLM fails.
    """
    key_map = {
        "openai":    config.OPENAI_API_KEY,
        "anthropic": config.ANTHROPIC_API_KEY,
        "gemini":    config.GEMINI_API_KEY,
    }

    try:
        if llm_provider == "openai":
            bible = _bible_openai(full_text, key_map["openai"])
        elif llm_provider == "anthropic":
            bible = _bible_anthropic(full_text, key_map["anthropic"])
        elif llm_provider == "gemini":
            bible = _bible_gemini(full_text, key_map["gemini"])
        else:
            bible = {}

        if not bible:
            raise ValueError("Empty bible returned")

        print(f"[prompt_engineer] Story bible: {bible}")
        return bible

    except Exception as e:
        print(f"[prompt_engineer] Story bible extraction failed: {e}. Using fallback.")
        return _fallback_bible(full_text)


def build_prompt(sentence: str, style: str, llm_provider: str, bible: dict = None) -> str:
    """
    Phase 2 — called once per panel.
    Uses the story bible to anchor visual consistency across all panels.

    Args:
        sentence:     One sentence from the segmented narrative.
        style:        Key from config.STYLES.
        llm_provider: 'openai' | 'anthropic' | 'gemini' | 'none'
        bible:        Story bible dict from extract_story_bible().

    Returns:
        Full SD-ready prompt string.
    """
    bible       = bible or {}
    bible_text  = _bible_to_text(bible)
    style_data  = config.STYLES.get(style, config.STYLES[config.DEFAULT_STYLE])
    style_suffix = style_data["suffix"] if isinstance(style_data, dict) else style_data

    key_map = {
        "openai":    config.OPENAI_API_KEY,
        "anthropic": config.ANTHROPIC_API_KEY,
        "gemini":    config.GEMINI_API_KEY,
    }

    try:
        if llm_provider == "openai":
            base = _panel_openai(sentence, style, bible_text, key_map["openai"])
        elif llm_provider == "anthropic":
            base = _panel_anthropic(sentence, style, bible_text, key_map["anthropic"])
        elif llm_provider == "gemini":
            base = _panel_gemini(sentence, style, bible_text, key_map["gemini"])
        else:
            base = _fallback_panel(sentence, style, bible)
    except Exception as e:
        print(f"[prompt_engineer] Panel prompt failed ({llm_provider}): {e}. Using fallback.")
        base = _fallback_panel(sentence, style, bible)

    return f"{base}, {style_suffix}"