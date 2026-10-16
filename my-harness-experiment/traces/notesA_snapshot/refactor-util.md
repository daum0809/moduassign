1) 접근법: 수정 전에 test_util.py를 먼저 읽어 요구사항(전 파라미터·반환 힌트, 독스트링 Args:/Returns:, None 가능한 곳은 Optional)을 확인한 뒤 util.py만 고쳤다.
2) 만난 오류: 없음. 첫 실행에서 `python test_util.py`가 4개 테스트 모두 OK였다(Ran 4 tests ... OK). 실패 사례가 없어 근거가 되는 실패 출력도 없다.
3) 해결 방법: 해당 없음. 다만 `list[T]`/`dict[str, int]` 표기는 Python 3.9+ 필요하며, 이 환경에서는 통과했다.
