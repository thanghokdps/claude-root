from pricing import apply_discount


def test_ten_percent():
    assert apply_discount(100, 10) == 90


def test_half_off():
    assert apply_discount(50, 50) == 25
