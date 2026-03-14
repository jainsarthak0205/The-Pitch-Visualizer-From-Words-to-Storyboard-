import nltk
import nltk
from nltk.tokenize import sent_tokenize

# Download required NLTK data on first run
def ensure_nltk_data():
    try:
        nltk.data.find("tokenizers/punkt_tab")
    except LookupError:
        nltk.download("punkt_tab", quiet=True)
    try:
        nltk.data.find("tokenizers/punkt")
    except LookupError:
        nltk.download("punkt", quiet=True)


def segment_text(text: str, min_segments: int = 3) -> list[dict]:
    """
    Splits input text into sentences using NLTK.
    Returns a list of dicts: [{index, text}, ...]

    If fewer than min_segments sentences are found, falls back to
    splitting on punctuation or splitting into rough thirds.
    """
    ensure_nltk_data()

    text = text.strip()
    sentences = sent_tokenize(text)

    # Filter out very short fragments (less than 5 words)
    sentences = [s.strip() for s in sentences if len(s.split()) >= 5]

    # Fallback: split on newlines if we don't have enough sentences
    if len(sentences) < min_segments:
        lines = [l.strip() for l in text.split("\n") if len(l.strip().split()) >= 5]
        if len(lines) >= min_segments:
            sentences = lines

    # Final fallback: chunk the full text into equal thirds
    if len(sentences) < min_segments:
        words = text.split()
        chunk_size = max(1, len(words) // min_segments)
        sentences = [
            " ".join(words[i : i + chunk_size])
            for i in range(0, len(words), chunk_size)
        ]
        sentences = sentences[:min_segments]

    return [{"index": i + 1, "text": s} for i, s in enumerate(sentences)]
