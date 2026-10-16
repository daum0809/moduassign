1) 접근법: 테스트를 먼저 실행해 실패 메시지를 확인하고, 테스트 파일은 수정하지 않고 소스(shop.py)만 고친 뒤 다시 실행해 통과를 확인한다.
2) 오류와 근거: `AssertionError: 2000.0 != 18000`(test_discount)에서 할인액을 반환하는 버그를, `2.67 != 2.68`(test_round_half_up)에서 내장 round()의 부동소수점 반올림 오차를 확인했다.
3) 해결: apply_discount는 `price * (100 - percent) / 100`로, round_price는 `Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)`로 바꿨다.
