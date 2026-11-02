from src.pagination import page


def test_first_page_starts_at_first_item():
    assert page(list(range(30)), 1, 10)[0] == 0


def test_second_page_starts_after_first():
    assert page(list(range(30)), 2, 10)[0] == 10
