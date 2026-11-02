from pricing import apply_discount


def test_zero_discount():
    assert apply_discount(100, 0) == 100


def test_returns_number():
    assert isinstance(apply_discount(80, 25), (int, float))
