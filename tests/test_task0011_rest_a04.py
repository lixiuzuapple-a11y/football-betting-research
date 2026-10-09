"""Synthetic regression checks for TASK-0011 rest calculation guards."""
import csv
import tempfile
import unittest
from pathlib import Path
from tools.task0011_rest_a04 import compute


class RestA04Tests(unittest.TestCase):
    def test_no_first_match_rest_and_no_future_information(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "small.csv"
            with path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=["lg", "season", "date", "home", "away", "PSH", "PSD", "PSA", "ftr"])
                writer.writeheader()
                for line in [
                    ("L", "2025", "01/01/25", "A", "B", "2", "3", "4", "H"),
                    ("L", "2025", "01/01/25", "C", "D", "2", "3", "4", "D"),
                    ("L", "2025", "02/01/25", "A", "C", "2", "3", "4", "A"),
                    ("L", "2025", "05/01/25", "B", "D", "2", "3", "4", "H"),
                    ("L", "2025", "06/01/25", "B", "A", "2", "3", "4", "D"),
                ]:
                    writer.writerow(dict(zip(writer.fieldnames, line)))
            r = compute(path)
            self.assertEqual(r["exclusions"]["no_prior_fixture"], 2)
            self.assertEqual(r["valid_rest_rows_before_price_filter"], 3)
            self.assertEqual(sum(v["n"] for v in r["groups"].values()), 3)
            self.assertEqual(r["source_rows_parsed"], 5)
            self.assertFalse(r["preregistered_adequacy_pass"])


if __name__ == "__main__":
    unittest.main()
