from dataclasses import dataclass

_next_id = 1


@dataclass
class Order:
    id: int
    total: int


def create_order(user_id, cart):
    global _next_id
    order = Order(_next_id, sum(item["price"] * item["qty"] for item in cart))
    _next_id += 1
    return order
