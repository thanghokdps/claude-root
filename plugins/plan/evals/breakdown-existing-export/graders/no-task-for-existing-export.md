---
type: llm
---

The repo already has the CSV export by date range: `export_orders_csv` in `app/orders.py` and the route `/admin/orders/export.csv` in `app/server.py`. Order listing by status and the refund email do not exist.

The skill asks its open questions before the task list, so the final reply may end on a question with the list still to come.

PASS if the reply says the export already exists with a file reference (`app/orders.py` or `app/server.py`) and gives it no task of its own (or only one that extends the existing code), and either shows the task list for confirmation — every task with Given/When/Then acceptance criteria and an estimate range with a stated basis — or asks its open questions first and names what each task will need.
FAIL if it writes a task to build the CSV export from scratch, gives estimates without a basis or as a bare point, or says it created issues on the tracker.
