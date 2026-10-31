import unittest

from shop.cart import total


class CartTest(unittest.TestCase):
    def test_total_sums_lines(self):
        self.assertEqual(total([{"price": 10, "qty": 2}, {"price": 5, "qty": 1}]), 25)

    def test_bulk_discount_over_100(self):
        items = [{"price": 60, "qty": 2}]
        self.assertEqual(total(items), 108.0)
