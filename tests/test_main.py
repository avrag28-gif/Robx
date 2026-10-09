import unittest
from datetime import datetime

from main import WIB, parse_sale_time, validate_shopee_url


class ValidationTests(unittest.TestCase):
    def test_accepts_shopee_indonesia_https(self):
        self.assertEqual(
            validate_shopee_url("https://shopee.co.id/product/123"),
            "https://shopee.co.id/product/123",
        )

    def test_rejects_non_shopee_domain(self):
        with self.assertRaises(Exception):
            validate_shopee_url("https://example.com/product")

    def test_rejects_http(self):
        with self.assertRaises(Exception):
            validate_shopee_url("http://shopee.co.id/product/123")

    def test_parses_wib_time(self):
        result = parse_sale_time("2026-10-10 12:30")
        self.assertEqual(result, datetime(2026, 10, 10, 12, 30, tzinfo=WIB))


if __name__ == "__main__":
    unittest.main()
