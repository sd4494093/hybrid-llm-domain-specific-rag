import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from verify_audit_feedback import exact_paired_p, verify


class FeedbackTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.evidence = Path(__file__).resolve().parents[1] / "evidence"
        labels = json.loads((cls.evidence / "proposed-system-evaluation/case-labels.json").read_text())
        cls.labels = {row["case_key"]: row["projection"] for row in labels["rows"]}

    def test_supplement_recounts_and_joins(self):
        result = verify(self.evidence / "audit-feedback", self.labels)
        self.assertEqual((result["strict_lost"], result["strict_gained"]), (119, 135))
        self.assertEqual(result["replay_answers_changed"], 11)

    def test_changed_output_fails_fingerprint(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "supplement"
            shutil.copytree(self.evidence / "audit-feedback", folder)
            path = folder / "ownership-crosswalk.json"
            data = json.loads(path.read_text())
            data["label_counts"]["partial"] = 411
            path.write_text(json.dumps(data))
            with self.assertRaises(AssertionError):
                verify(folder, self.labels)

    def test_changed_public_label_fails_join(self):
        labels = dict(self.labels)
        key = next(iter(labels))
        labels[key] = {**labels[key], "label": "partial" if labels[key]["label"] != "partial" else "incorrect"}
        with self.assertRaises(AssertionError):
            verify(self.evidence / "audit-feedback", labels)

    def test_exact_paired_test(self):
        self.assertAlmostEqual(exact_paired_p(119, 135), 0.3466, places=3)
        self.assertEqual(exact_paired_p(0, 0), 1.0)


if __name__ == "__main__":
    unittest.main()
