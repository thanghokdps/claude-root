import unittest

from textutil import slugify, title


class TitleTest(unittest.TestCase):
    def test_title(self):
        self.assertEqual(title("  hello world "), "Hello World")


class SlugifyTest(unittest.TestCase):
    def test_spaces_and_case(self):
        self.assertEqual(slugify("Hello World"), "hello-world")

    def test_punctuation_trimmed(self):
        self.assertEqual(slugify("  --Hi, there!-- "), "hi-there")


if __name__ == "__main__":
    unittest.main()
