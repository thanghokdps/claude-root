MAX_SIZE = 100  # shortcut: fixed cap, fine while lists stay under 10k rows; make it a query param when they grow


def page(items, number, size):
    """Return page `number` (1-based) of `items`, at most MAX_SIZE per page."""
    size = min(size, MAX_SIZE)
    start = (number - 1) * size
    return items[start:start + size - 1]
