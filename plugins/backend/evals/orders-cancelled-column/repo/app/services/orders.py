from app.errors import AppError
from app.repositories import orders as repo


def get_order_for_user(db, user, order_id: int):
    order = repo.get_order(db, user.id, order_id)
    if order is None:
        raise AppError(404, "order_not_found", "Order not found")
    return order
