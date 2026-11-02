import unittest

from todo.store import TodoStore


class TodoStoreTest(unittest.TestCase):
    def test_add_returns_incrementing_ids(self):
        store = TodoStore()
        self.assertEqual(store.add("a"), 1)
        self.assertEqual(store.add("b"), 2)

    def test_done_marks_task(self):
        store = TodoStore()
        task_id = store.add("a")
        store.done(task_id)
        self.assertTrue(store.list()[0]["done"])


if __name__ == "__main__":
    unittest.main()
