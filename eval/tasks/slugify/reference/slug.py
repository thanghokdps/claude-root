import re


def slugify(text):
    """Lowercase text, replace spaces and punctuation with hyphens."""
    lowered = text.lower()
    hyphenated = re.sub(r"[^a-z0-9]+", "-", lowered)
    return hyphenated.strip("-")
