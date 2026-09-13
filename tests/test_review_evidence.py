import io
import json
from pathlib import Path
import sys
import subprocess
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from build_review_evidence import (PAGE_BYTES, numeric_project, stream_project,
                                   supplement, version_dir, write_pages)
from export_evidence import digest


def restore(folder, value):
    if isinstance(value, dict):
        if set(value) == {"review_pages", "item_count"}:
            rows = []
            for rel in value["review_pages"]:
                rows.extend(restore(folder, json.loads((folder / rel).read_text())))
            assert len(rows) == value["item_count"]
            return rows
        return {key: restore(folder, child) for key, child in value.items()}
    if isinstance(value, list):
        return [restore(folder, child) for child in value]
    return value


class ReviewTests(unittest.TestCase):
    def test_v1617_array_false_and_missing_rank(self):
        data = {"case_count": 3, "dataset_id": "private", "results": [
            {"expected_in_candidates": False, "expected_parent_vector_rank": 57,
             "expected_parent_full_text_rank": None, "question": "secret",
             "selector_results": {"semantic": {"expected_selected": False,
                 "selected_parent_ids": ["private"], "selected_parent_count": 5}}}, {}, {}]}
        safe = numeric_project(data)
        self.assertEqual(len(safe["results"]), 3)
        self.assertFalse(safe["results"][0]["expected_in_candidates"])
        self.assertIsNone(safe["results"][0]["expected_parent_full_text_rank"])
        self.assertNotIn("private", json.dumps(safe))
        self.assertNotIn("secret", json.dumps(safe))
        self.assertEqual(safe, numeric_project(safe))

    def test_unknown_keys_and_nonfinite_numbers(self):
        self.assertEqual(numeric_project({"count": float("nan"), "rank": "credential", "api_key": 42,
            "results": [{"secret_customer": {"count": 1}, "score": float("inf")}]}), {"results": [{}]})

    def test_stream_matches_in_memory(self):
        try:
            import ijson  # noqa: F401
        except ImportError:
            self.skipTest("Private-source export requires tools/requirements-export.txt")
        data = {"case_count": 3, "results": [{"rank": 1, "expected_selected": False,
            "full_text_rank": None, "answer": {"results": [{"score": 999}]},
            "candidate_numeric_surface": [{"rank": 2, "parent_id": "secret"}]}, {}, "secret"]}
        self.assertEqual(stream_project(io.BytesIO(json.dumps(data).encode())), numeric_project(data))

    def test_missing_changed_and_matching_sources(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "results.jsonl"
            raw = b'{"rank": 57, "expected_selected": false}\n'
            p.write_bytes(raw)
            inv = {"bytes": len(raw), "source_sha256": digest(raw)}
            self.assertEqual(supplement(None, inv), ("source_missing", None))
            self.assertEqual(supplement(p, inv)[0], "numeric_content")
            p.write_bytes(raw.replace(b"57", b"58"))
            self.assertEqual(supplement(p, inv), ("source_changed_since_inventory", None))

    def test_recursive_pagination_is_lossless_and_bounded(self):
        data = {"results": [{"rank": i, "rows": [{"score": j} for j in range(120)]}
                            for i in range(203)]}
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            write_pages(folder, data)
            self.assertEqual(restore(folder, json.loads((folder / "data.json").read_text())), data)
            for path in folder.rglob("*.json"):
                self.assertLessEqual(path.stat().st_size, PAGE_BYTES)
            for path in folder.rglob("*"):
                if path.is_dir():
                    self.assertLessEqual(len(list(path.iterdir())), 100)

    def test_all_1660_versions_are_sharded(self):
        buckets = {}
        for v in range(1, 1661):
            p = version_dir(Path("evidence"), v)
            buckets.setdefault(p.parent, []).append(v)
        self.assertEqual(len(buckets), 34)
        self.assertTrue(all(len(vs) <= 50 for vs in buckets.values()))

    def test_renamed_evidence_anchors_recompute(self):
        root = Path(__file__).resolve().parents[1]
        result = subprocess.run([sys.executable, str(root / "framework/evaluation/recompute.py")],
                                check=True, capture_output=True, text=True)
        records = [json.loads(line) for line in result.stdout.splitlines()]
        self.assertEqual(records[1]["semantic_numerator"], 1451)
        self.assertEqual(records[-1]["v1660_paper_reporting"]["numerator"], 1862)


if __name__ == "__main__":
    unittest.main()
