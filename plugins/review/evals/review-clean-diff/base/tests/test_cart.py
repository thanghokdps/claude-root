from src.cart import total


def test_total():
    assert total([{"price": 2, "qty": 3}, {"price": 5, "qty": 1}]) == 11


def test_total_of_empty_cart_is_zero():
    assert total([]) == 0
