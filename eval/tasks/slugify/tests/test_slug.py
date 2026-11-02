from slug import slugify


def test_basic():
    assert slugify("Hello World") == "hello-world"


def test_punctuation():
    assert slugify("A, B & C!") == "a-b-c"


def test_trim():
    assert slugify("  spaced  ") == "spaced"
