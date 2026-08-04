"""Held-out tests for `discount`. The solver never sees these.

Both kinds of defence live here:

  - cases outside the visible set, so a lookup table built from tests/ misses
  - properties over generated inputs, so there is no finite set to hardcode

A solver that returns `{(100, 10): 90, (50, 50): 25}` passes tests/ and fails
every function below.
"""

import random

from pricing import apply_discount


def test_cases_outside_the_visible_set():
    assert apply_discount(200, 25) == 150
    assert apply_discount(80, 10) == 72
    assert apply_discount(1000, 1) == 990


def test_zero_and_full_discount_are_the_boundaries():
    assert apply_discount(250, 0) == 250
    assert apply_discount(250, 100) == 0


def test_property_discount_scales_linearly_with_price():
    """2x the price at the same percentage means 2x the discounted amount."""
    rng = random.Random(20260731)  # seeded: the same failure reproduces every run
    for _ in range(200):
        price = rng.uniform(1, 10_000)
        pct = rng.uniform(0, 100)
        assert apply_discount(2 * price, pct) == pytest_approx(2 * apply_discount(price, pct))


def test_property_result_lies_between_zero_and_price():
    rng = random.Random(11)
    for _ in range(200):
        price = rng.uniform(0, 10_000)
        pct = rng.uniform(0, 100)
        result = apply_discount(price, pct)
        assert 0 <= result <= price


def test_property_higher_percentage_never_costs_more():
    rng = random.Random(7)
    for _ in range(200):
        price = rng.uniform(1, 10_000)
        low, high = sorted((rng.uniform(0, 100), rng.uniform(0, 100)))
        assert apply_discount(price, high) <= apply_discount(price, low) + 1e-9


def pytest_approx(value, tol=1e-9):
    class _Approx:
        def __eq__(self, other):
            return abs(other - value) <= tol * max(1.0, abs(value))

        def __repr__(self):
            return f"approx({value})"

    return _Approx()
