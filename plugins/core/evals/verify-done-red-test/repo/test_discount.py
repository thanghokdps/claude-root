import unittest

from discount import apply_discount


class DiscountTest(unittest.TestCase):
    def test_ten_percent(self):
        self.assertEqual(apply_discount(200, 10), 180)

    def test_zero_percent(self):
        self.assertEqual(apply_discount(50, 0), 50)

    def test_discount_caps_at_100(self):
        self.assertEqual(apply_discount(100, 150), 0)


if __name__ == "__main__":
    unittest.main()
