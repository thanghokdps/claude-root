"""Order list for the admin screen."""
from datetime import datetime, timedelta

ORDERS = [
    {"id": 1, "customer": "an", "total": 120.0, "created": datetime(2026, 1, 3)},
    {"id": 2, "customer": "binh", "total": 80.5, "created": datetime(2026, 2, 20)},
]


def list_orders(now, days=None):
    if days is None:
        return list(ORDERS)
    cutoff = now - timedelta(days=days)
    return [o for o in ORDERS if o["created"] >= cutoff]


def is_admin(user):
    return user.get("role") == "admin"
