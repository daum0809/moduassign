"""parse-log 작업 확인용 테스트. 이 파일은 수정하지 않는다."""
import subprocess
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).parent


class ParseLogTest(unittest.TestCase):
    def test_parse_errors_returns_only_error_level(self):
        from parse import parse_errors
        rows = parse_errors(HERE / "sample.log")
        self.assertEqual(
            rows,
            [
                {"time": "2026-10-01 09:02:30", "module": "db",
                 "message": "connection refused: 10.0.0.5:5432"},
                {"time": "2026-10-01 09:03:44", "module": "auth",
                 "message": "token expired for user_id=42"},
                {"time": "2026-10-01 09:07:03", "module": "payment",
                 "message": "amount | currency mismatch"},
            ],
        )

    def test_cli_prints_markdown_table(self):
        out = subprocess.run(
            [sys.executable, str(HERE / "parse.py"), str(HERE / "sample.log")],
            capture_output=True, text=True, encoding="utf-8", check=True,
        ).stdout
        self.assertEqual(
            out.strip().splitlines(),
            [
                "| time | module | message |",
                "|---|---|---|",
                "| 2026-10-01 09:02:30 | db | connection refused: 10.0.0.5:5432 |",
                "| 2026-10-01 09:03:44 | auth | token expired for user_id=42 |",
                "| 2026-10-01 09:07:03 | payment | amount \| currency mismatch |",
            ],
        )


if __name__ == "__main__":
    unittest.main()
