_cache: list = []


def remember(orders: list) -> None:
    _cache[:] = orders


def cached_orders() -> list:
    return list(_cache)
