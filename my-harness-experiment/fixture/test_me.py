"""fix-failing 작업 확인용 테스트. 이 파일은 수정하지 않는다."""
import unittest

from shop import apply_discount, round_price


class ShopTest(unittest.TestCase):
    def test_discount(self):
        self.assertEqual(apply_discount(20000, 10), 18000)
        self.assertEqual(apply_discount(15000, 0), 15000)

    def test_round_half_up(self):
        self.assertEqual(round_price(2.675), 2.68)
        self.assertEqual(round_price(1.005), 1.01)
        self.assertEqual(round_price(0.125), 0.13)
        self.assertEqual(round_price(3.14159), 3.14)


if __name__ == "__main__":
    unittest.main()
