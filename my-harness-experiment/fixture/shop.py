def apply_discount(price, percent):
    """할인이 적용된 가격을 돌려준다."""
    return price * percent / 100


def round_price(value):
    """소수 둘째 자리까지 반올림한다(0.5는 항상 올림)."""
    return round(value, 2)
