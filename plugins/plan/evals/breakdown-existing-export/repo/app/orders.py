import csv
import io
from datetime import date

ORDERS = [
    {"id": 1, "status": "paid", "total": 120, "placed_on": date(2026, 1, 3)},
    {"id": 2, "status": "refunded", "total": 80, "placed_on": date(2026, 1, 9)},
]


def refund_order(order_id):
    for order in ORDERS:
        if order["id"] == order_id:
            order["status"] = "refunded"
            return order
    raise KeyError(order_id)


def export_orders_csv(start, end):
    """Orders placed between start and end (inclusive) as CSV text."""
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(["id", "status", "total", "placed_on"])
    for o in ORDERS:
        if start <= o["placed_on"] <= end:
            writer.writerow([o["id"], o["status"], o["total"], o["placed_on"].isoformat()])
    return out.getvalue()
