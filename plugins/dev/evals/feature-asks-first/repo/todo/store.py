"""In-memory todo store."""


class TodoStore:
    def __init__(self):
        self._tasks = {}
        self._next_id = 1

    def add(self, title):
        task_id = self._next_id
        self._next_id += 1
        self._tasks[task_id] = {"id": task_id, "title": title, "done": False}
        return task_id

    def list(self):
        return list(self._tasks.values())

    def done(self, task_id):
        self._tasks[task_id]["done"] = True
