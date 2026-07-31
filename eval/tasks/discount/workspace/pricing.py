def apply_discount(price, pct):
    """Return price after applying a percentage discount."""
    # BUG: treats pct as a fraction, not a percentage.
    return price - price * pct
