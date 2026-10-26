import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from env_key_matrix import compare, main, scan_file


class EnvKeyMatrixTests(unittest.TestCase):
    def test_reports_presence_without_values(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            local = root / ".env.local"
            prod = root / ".env.prod"
            local.write_text("API_TOKEN=local-secret\nSHARED=yes\n", encoding="utf-8")
            prod.write_text("API_TOKEN=prod-secret\nDATABASE_URL=hidden-value\n", encoding="utf-8")
            rows, issues = compare([local, prod])
            rendered = json.dumps({"keys": rows, "issues": issues})
            self.assertNotIn("local-secret", rendered)
            self.assertNotIn("prod-secret", rendered)
            self.assertEqual(issues, [])
            self.assertEqual(rows[0], {"key": "API_TOKEN", "present_in": [str(local), str(prod)]})

    def test_detects_duplicate_and_malformed_without_value_disclosure(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / ".env"
            path.write_text("TOKEN=top-secret\nTOKEN=rotated-secret\nbroken top-secret\n", encoding="utf-8")
            _, issues = scan_file(path)
            self.assertEqual([item["kind"] for item in issues], ["duplicate-key", "malformed-line"])
            self.assertNotIn("top-secret", str(issues))

    def test_json_exit_code_signals_key_drift(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            one, two = root / "one.env", root / "two.env"
            one.write_text("A=1\n", encoding="utf-8")
            two.write_text("B=2\n", encoding="utf-8")
            output = io.StringIO()
            with redirect_stdout(output):
                result = main([str(one), str(two), "--json"])
            self.assertEqual(result, 1)
            payload = json.loads(output.getvalue())
            self.assertEqual(len(payload["keys"]), 2)


if __name__ == "__main__":
    unittest.main()
