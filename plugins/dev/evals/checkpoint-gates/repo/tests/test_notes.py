import unittest

from notes import notes


class NotesTest(unittest.TestCase):
    def setUp(self):
        notes.NOTES.clear()

    def test_add_note(self):
        notes.add_note("a", ["x"])
        self.assertEqual(len(notes.NOTES), 1)

    def test_list_newest_first(self):
        notes.add_note("a")
        notes.add_note("b")
        self.assertEqual([n["text"] for n in notes.list_notes()], ["b", "a"])

    def test_search_by_tag(self):
        notes.add_note("a", ["x"])
        notes.add_note("b", ["y"])
        self.assertEqual([n["text"] for n in notes.search_by_tag("x")], ["a"])
