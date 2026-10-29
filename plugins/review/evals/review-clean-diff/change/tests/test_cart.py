from src.cart import item_count, total


def test_total():
    assert total([{"price": 2, "qty": 3}, {"price": 5, "qty": 1}]) == 11


def test_total_of_empty_cart_is_zero():
    assert total([]) == 0


def test_item_count_sums_quantities():
    assert item_count([{"price": 2, "qty": 3}, {"price": 5, "qty": 1}]) == 4


def test_item_count_of_empty_cart_is_zero():
    assert item_count([]) == 0
