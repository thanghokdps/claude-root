from app.models import Order


def get_order(db, owner_id: int, order_id: int) -> Order | None:
    row = db.execute(
        "SELECT id, user_id, total_cents, status, created_at FROM orders WHERE id = ? AND user_id = ?",
        (order_id, owner_id),
    ).fetchone()
    return Order(*row) if row else None


def list_orders(db, owner_id: int, limit: int = 20) -> list[Order]:
    rows = db.execute(
        "SELECT id, user_id, total_cents, status, created_at FROM orders WHERE user_id = ? ORDER BY id DESC LIMIT ?",
        (owner_id, limit),
    ).fetchall()
    return [Order(*r) for r in rows]
