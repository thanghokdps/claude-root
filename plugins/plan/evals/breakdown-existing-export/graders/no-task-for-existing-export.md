---
type: llm
---

The repo already has the CSV export by date range: `export_orders_csv` in `app/orders.py` and the route `/admin/orders/export.csv` in `app/server.py`. Order listing by status and the refund email do not exist.

PASS if the reply shows a task list for confirmation in which the CSV export gets no task of its own (or only a task that extends the existing code and names `app/orders.py` or `app/server.py`), says the export already exists with a file reference, and every task has Given/When/Then acceptance criteria and an estimate range with a stated basis.
FAIL if it writes a task to build the CSV export from scratch, gives estimates without a basis or as a bare point, or says it created issues on the tracker.
