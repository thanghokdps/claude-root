import unittest

from src.orders import list_orders


class OrdersTest(unittest.TestCase):
    def test_page_size(self):
        self.assertEqual(len(list_orders(1, 20)), 20)


if __name__ == "__main__":
    unittest.main()
