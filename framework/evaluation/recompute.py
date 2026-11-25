#!/usr/bin/env python3
"""Recompute public label and E2E counts without access to private text."""

import collections
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from export_conventional_baseline import FLAGS, summarize


def main():
    evidence = ROOT / "evidence"
    for folder in ("baseline-system-evaluation", "proposed-system-evaluation"):
        rows = json.loads((evidence / folder / "case-labels.json").read_text())["rows"]
        counts = collections.Counter(r["projection"]["label"] for r in rows)
        assert len(rows) == 2000 and len({r["case_key"] for r in rows}) == 2000
        summary = json.loads((evidence / folder / "summary.json").read_text())
        assert counts == summary["recomputed_labels"]
        numerator = counts["correct"] + counts["correct_refusal"]
        print(json.dumps({"evaluation": folder, "labels": counts, "semantic_numerator": numerator,
                          "denominator": len(rows), "rate": numerator / len(rows)}))
    rows = json.loads((evidence / "proposed-system-evaluation/case-evaluation.json").read_text())["rows"]
    count = sum(r["projection"]["judgment"]["e2e_pass"] for r in rows)
    assert len(rows) == 2000 and count == 1422
    print(json.dumps({"v1660_e2e": count, "denominator": len(rows), "rate": count / len(rows)}))
    proposed = {r["case_key"]: r["projection"]["judgment"] for r in rows}
    path = evidence / "baseline-system-evaluation"
    control = json.loads((path / "case-labels.json").read_text())["rows"]
    baseline = json.loads((path / "summary.json").read_text())
    counts, metrics = summarize(control)
    assert counts == baseline["recomputed_labels"] and metrics == baseline["metrics"]
    assert {r["case_key"] for r in control} == proposed.keys()
    assert baseline["first_attempt_success_count"] + baseline["recovered_after_retry_count"] == metrics["runtime_ok"]["count"] == 2000
    assert baseline["judge_errors"] == baseline["judge_skips"] == 0
    transitions = collections.defaultdict(collections.Counter)
    for row in control:
        a, b = row["projection"], proposed[row["case_key"]]
        assert set(row) == {"case_key", "projection"}
        assert set(a) == {"label", "expected_answer_type", *FLAGS}
        assert all(type(a[k]) is bool for k in FLAGS)
        assert a["expected_answer_type"] == b["expected_answer_type"]
        strict = {"correct", "correct_refusal"}
        for metric, labels in (("strict", strict), ("strict_or_partial", strict | {"partial"})):
            transitions[metric][a["label"] in labels, b["semantic_judge_label"] in labels] += 1
        transitions["e2e"][a["e2e_pass"], b["e2e_pass"] is True] += 1
        a_strict_e2e = (a["label"] in strict
                        and (a["expected_answer_type"] != "grounded" or a["exact_source_recall_at_10"])
                        and a["e2e_pass"])
        b_strict_e2e = (b["semantic_judge_label"] in strict
                        and (b["expected_answer_type"] != "grounded" or b["exact_source_recall_at_10"] is True)
                        and b["e2e_pass"] is True)
        transitions["strict_source_at_10_e2e"][a_strict_e2e, b_strict_e2e] += 1
        if a["expected_answer_type"] == "grounded":
            for metric in ("exact_source_recall_at_10",):
                transitions[metric][a[metric], b[metric] is True] += 1
    assert baseline["paired_deltas"] == {
        metric: {"denominator": sum(c.values()), "both_pass": c[True, True], "both_fail": c[False, False],
                 "gain_v1660": c[False, True], "loss_v1660": c[True, False]}
        for metric, c in transitions.items()
    }
    print(json.dumps({"paired_control": metrics}))

    # Semantic outcomes and diagnostic ownership are separate classifications.
    folder = evidence / "proposed-system-evaluation"
    reporting = json.loads((folder / "paper-reporting.json").read_text())
    summary = json.loads((folder / "summary.json").read_text())
    buckets = summary["failure_cohort_buckets"]
    strict = summary["quality_metrics"]["semantic_correctness_rate"]["numerator"]
    labels = summary["recomputed_labels"]
    partial = labels["partial"]
    remaining = labels["incorrect"] + labels["incorrect_refusal"]
    assert strict + partial + remaining == reporting["total"] == 2000
    assert reporting["diagnostic_ownership"] == buckets
    assert reporting["remaining_labels"] == {k: labels[k] for k in ("incorrect", "incorrect_refusal")}
    for key, expected in (("strict_semantic_correct", strict), ("partially_correct", partial),
                          ("remaining", remaining), ("correct_or_partial", strict + partial)):
        metric = reporting[key]
        assert metric["numerator"] == expected and metric["denominator"] == 2000
        assert abs(metric["rate"] - expected / 2000) < 1e-12
    print(json.dumps({"v1660_paper_reporting": reporting["correct_or_partial"],
                      "original_partial_labels": partial,
                      "diagnostic_planner_assignments": buckets["planner/partial"]}))


if __name__ == "__main__":
    main()
