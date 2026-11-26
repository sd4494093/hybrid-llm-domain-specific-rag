import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

from recover_version_evidence import measurements


class VersionRecoveryTests(unittest.TestCase):
    def test_jsonl_preserves_complete_rows_before_truncated_tail(self):
        data = (b'{"judgment":{"semantic_judge_label":"correct","e2e_pass":true},"answer":"private"}\n'
                b'{"judgment":{"semantic_judge_status":"error","e2e_pass":false}}\n'
                b'{"judgment":')
        self.assertEqual(measurements(data, ".jsonl"), ([
            {"line": 1, "measurements": {"judgment": {"semantic_judge_label": "correct", "e2e_pass": True}}},
            {"line": 2, "measurements": {"judgment": {"semantic_judge_status": "error", "e2e_pass": False}}},
        ], 1))

    def test_csv_uses_same_allowlist(self):
        data = b"case_id,expected_in_candidates,vector_rank\nprivate,false,57\nprivate,true,9\n"
        self.assertEqual(measurements(data, ".csv"), ([
            {"line": 2, "measurements": {"expected_in_candidates": False, "vector_rank": 57}},
            {"line": 3, "measurements": {"expected_in_candidates": True, "vector_rank": 9}},
        ], 0))

    def test_exit_status_is_not_a_case_outcome(self):
        self.assertEqual(measurements(b"124\n", ".exit"), ({"exit_code": 124}, 0))
