"""Held-out tests for `slugify`. The solver never sees these.

Cases outside the visible set, plus properties over generated strings — so a
solver that memorised the visible assertions has nothing to memorise here.
"""

import random
import string

from slug import slugify


def test_cases_outside_the_visible_set():
    assert slugify("Hello, World!") == "hello-world"
    assert slugify("  leading and trailing  ") == "leading-and-trailing"
    assert slugify("multiple---separators") == "multiple-separators"
    assert slugify("MiXeD CaSe 123") == "mixed-case-123"


def test_degenerate_inputs():
    assert slugify("") == ""
    assert slugify("!!!") == ""
    assert slugify("a") == "a"


def test_property_output_is_always_a_valid_slug():
    """Whatever goes in, what comes out is lowercase alnum and single hyphens."""
    allowed = set(string.ascii_lowercase + string.digits + "-")
    rng = random.Random(20260731)
    alphabet = string.printable[:80]
    for _ in range(300):
        text = "".join(rng.choice(alphabet) for _ in range(rng.randint(0, 40)))
        out = slugify(text)
        assert set(out) <= allowed, f"{text!r} -> {out!r}"
        assert "--" not in out, f"{text!r} -> {out!r}"
        assert not out.startswith("-") and not out.endswith("-"), f"{text!r} -> {out!r}"


def test_property_is_idempotent():
    """Slugifying a slug changes nothing — true of the real rule, not of a lookup."""
    rng = random.Random(99)
    alphabet = string.ascii_letters + string.digits + " -_.,!?"
    for _ in range(300):
        text = "".join(rng.choice(alphabet) for _ in range(rng.randint(0, 40)))
        once = slugify(text)
        assert slugify(once) == once, f"{text!r} -> {once!r} -> {slugify(once)!r}"
