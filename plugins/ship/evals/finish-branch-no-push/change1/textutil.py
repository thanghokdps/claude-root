import re


def title(s: str) -> str:
    return s.strip().title()


def slugify(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
