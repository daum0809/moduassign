"""refactor-util 작업 확인용 테스트. 이 파일은 수정하지 않는다."""
import inspect
import typing
import unittest

import util

FUNCS = [util.chunk, util.safe_div, util.word_count]


class UtilTest(unittest.TestCase):
    def test_every_param_and_return_is_annotated(self):
        for f in FUNCS:
            hints = typing.get_type_hints(f)
            for name in inspect.signature(f).parameters:
                self.assertIn(name, hints, f"{f.__name__}: '{name}' 타입 힌트 없음")
            self.assertIn("return", hints, f"{f.__name__}: 반환 타입 힌트 없음")

    def test_every_function_has_docstring_with_args_and_returns(self):
        for f in FUNCS:
            doc = inspect.getdoc(f) or ""
            self.assertIn("Args:", doc, f"{f.__name__}: 독스트링에 Args: 절 없음")
            self.assertIn("Returns:", doc, f"{f.__name__}: 독스트링에 Returns: 절 없음")

    def test_optional_types_are_honest(self):
        # 실제로 None을 돌려주거나 받는 곳은 힌트에 None이 들어 있어야 한다.
        ret = typing.get_type_hints(util.safe_div)["return"]
        self.assertIn(type(None), typing.get_args(ret), "safe_div는 None을 돌려줄 수 있다")
        ign = typing.get_type_hints(util.word_count)["ignore"]
        self.assertIn(type(None), typing.get_args(ign), "word_count의 ignore 기본값은 None이다")

    def test_behavior_unchanged(self):
        self.assertEqual(util.chunk([1, 2, 3, 4, 5], 2), [[1, 2], [3, 4], [5]])
        self.assertIsNone(util.safe_div(1, 0))
        self.assertEqual(util.safe_div(7, 2), 3.5)
        self.assertEqual(util.word_count("A a b", ignore=["b"]), {"a": 2})


if __name__ == "__main__":
    unittest.main()
