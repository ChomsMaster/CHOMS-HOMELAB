import gzip
import json
import tempfile
import unittest
from pathlib import Path

import seed


class SeedTest(unittest.TestCase):
    def setUp(self):
        self.record = {
            "id": "example-2028-01-02",
            "date": "2028-01-02",
            "start": "22:00",
            "end": "24:00",
            "title": "Example",
            "kind": "focus",
            "notes": "",
            "provisional": True,
        }
        self.data = {
            "project": {"start": "2028-01-01", "end": "2028-01-03"},
            "tasks": [{"id": "task-example", "title": "Example task"}],
            "plan": {"moto": [self.record], "publico": []},
        }

    def load(self, suffix=".json"):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / ("seed" + suffix)
            raw = json.dumps(self.data).encode()
            path.write_bytes(gzip.compress(raw) if suffix == ".gz" else raw)
            return seed.load_seed(path)

    def test_seed_is_optional(self):
        project, tasks, plan = seed.load_seed(None)
        self.assertEqual(project, {})
        self.assertEqual(tasks, [])
        self.assertEqual(plan, {})

    def test_plain_and_gzipped_seed(self):
        plain = self.load()
        self.assertEqual(plain, self.load(".gz"))
        self.assertEqual(plain, tuple(self.data.values()))

    def test_reject_duplicate_occurrences(self):
        self.data["plan"]["moto"].append(dict(self.record))
        with self.assertRaisesRegex(RuntimeError, "^CAREER_SEED_FILE is invalid or unreadable$"):
            self.load()

    def test_reject_out_of_bounds_records(self):
        self.record["date"] = "2028-01-04"
        with self.assertRaises(RuntimeError):
            self.load()

    def test_reject_invalid_hours(self):
        self.record["start"] = "24:00"
        with self.assertRaises(RuntimeError):
            self.load()

if __name__ == "__main__":
    unittest.main()
