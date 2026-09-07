import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from export_evidence import project, versions

spec = importlib.util.spec_from_file_location("gates", ROOT / "framework/quality-gates/run_pipeline.py")
gates = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gates)


class ProjectionTests(unittest.TestCase):
    def test_unknown_text_and_nested_identity_are_dropped(self):
        payload = {"question": "private prompt", "answer": "private answer", "api_key": "credential",
                   "label": "correct", "failure_classes": {"private_customer_name": 1, "semantic_incomplete": 2},
                   "model": {"api_key": "credential"}, "quality_metrics": {"semantic_correctness_rate": {"numerator": 3, "denominator": 5, "rate": 0.6}},
                   "status": "private free text", "answer_sha256": "not-a-hash"}
        self.assertEqual(project(payload), {"label": "correct", "failure_classes": {"semantic_incomplete": 2},
                         "quality_metrics": {"semantic_correctness_rate": {"numerator": 3, "denominator": 5, "rate": 0.6}}})

    def test_hash_and_verdict_preserved(self):
        row = {"answer_sha256": "a" * 64, "semantic_label": "partial", "judgment": {"e2e_pass": False, "reason": "private"}}
        expected = {"answer_sha256": "a" * 64, "semantic_label": "partial", "judgment": {"e2e_pass": False}}
        self.assertEqual(project(row), expected)
        self.assertEqual(project(expected), expected)

    def test_owning_layer_counts_remain_separate(self):
        row = {"failure_buckets": {"planner/partial": 411, "citation/source": 30, "no-answer": 108}}
        self.assertEqual(project(row), row)

    def test_nonfinite_metrics_dropped(self):
        self.assertEqual(project({"rate": float("nan"), "count": float("inf")}), {})

    def test_version_range_and_mentions(self):
        self.assertEqual(versions("v0100 against v1441; v1660; v1661; shaabv3; v16601"), [100, 1441, 1660])


class GateTests(unittest.TestCase):
    def setUp(self):
        self.policy = json.loads((ROOT / "framework/quality-gates/config.json").read_text())
        self.text = "A synthetic document with enough text for the structural gate to accept its length."

    def test_missing_ai_verdict_never_passes(self):
        self.assertEqual(gates.evaluate(self.text, self.policy)["status"], "needs_review")
        self.assertEqual(gates.evaluate("", self.policy)["status"], "rule_failed")

    def test_bound_verdict_and_changed_content(self):
        verdict = {"content_sha256": hashlib.sha256(self.text.encode()).hexdigest(),
                   "policy_version": self.policy["policy_version"], "evaluator_version": "synthetic-v1", "verdict": "pass"}
        self.assertEqual(gates.evaluate(self.text, self.policy, verdict)["status"], "ai_passed")
        self.assertEqual(gates.evaluate(self.text + " changed", self.policy, verdict)["status"], "needs_review")
        verdict["policy_version"] = "different"
        self.assertEqual(gates.evaluate(self.text, self.policy, verdict)["status"], "needs_review")


if __name__ == "__main__":
    unittest.main()
