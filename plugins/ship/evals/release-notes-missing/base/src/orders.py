def list_orders(page: int = 1, size: int = 20) -> list:
    return [{"id": i} for i in range((page - 1) * size, page * size)]
