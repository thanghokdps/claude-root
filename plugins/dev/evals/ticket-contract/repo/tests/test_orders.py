import unittest
from datetime import datetime

from shop.orders import is_admin, list_orders


class OrdersTest(unittest.TestCase):
    def test_days_filter(self):
        orders = list_orders(datetime(2026, 2, 25), days=30)
        self.assertEqual([o["id"] for o in orders], [2])

    def test_is_admin(self):
        self.assertTrue(is_admin({"role": "admin"}))
        self.assertFalse(is_admin({"role": "staff"}))
