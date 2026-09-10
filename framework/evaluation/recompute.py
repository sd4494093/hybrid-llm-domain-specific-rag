#!/usr/bin/env python3
"""Recompute public label and E2E counts without access to private text."""

import collections
import json
from pathlib import Path


def main():
    evidence = Path(__file__).resolve().parents[2] / "evidence"
    for folder in ("baseline-UAT-20260608", "v1660-final-baseline"):
        rows = json.loads((evidence / folder / "case-labels.json").read_text())["rows"]
        counts = collections.Counter(r["projection"]["label"] for r in rows)
        assert len(rows) == 2000 and len({r["case_key"] for r in rows}) == 2000
        summary = json.loads((evidence / folder / "summary.json").read_text())
        assert counts == summary["recomputed_labels"]
        numerator = counts["correct"] + (counts["correct_refusal"] if folder.startswith("v") else 0)
        print(json.dumps({"evaluation": folder, "labels": counts, "semantic_numerator": numerator,
                          "denominator": len(rows), "rate": numerator / len(rows)}))
    rows = json.loads((evidence / "v1660-final-baseline/case-evaluation.json").read_text())["rows"]
    count = sum(r["projection"]["judgment"]["e2e_pass"] for r in rows)
    assert len(rows) == 2000 and count == 1422
    print(json.dumps({"v1660_e2e": count, "denominator": len(rows), "rate": count / len(rows)}))

    # The paper groups recovery ownership separately from automated Judge labels.
    folder = evidence / "v1660-final-baseline"
    reporting = json.loads((folder / "paper-reporting.json").read_text())
    summary = json.loads((folder / "summary.json").read_text())
    buckets = summary["failure_cohort_buckets"]
    strict = summary["quality_metrics"]["semantic_correctness_rate"]["numerator"]
    partial = buckets["planner/partial"]
    remaining = buckets["no-answer"] + buckets["citation/source"]
    assert strict + partial + remaining == reporting["total"] == 2000
    assert reporting["remaining_ownership"] == {k: buckets[k] for k in ("no-answer", "citation/source")}
    for key, expected in (("strict_semantic_correct", strict), ("partially_correct", partial),
                          ("remaining", remaining), ("correct_or_partial", strict + partial)):
        metric = reporting[key]
        assert metric["numerator"] == expected and metric["denominator"] == 2000
        assert abs(metric["rate"] - expected / 2000) < 1e-12
    print(json.dumps({"v1660_paper_reporting": reporting["correct_or_partial"],
                      "partially_correct_recovery_cases": partial}))


if __name__ == "__main__":
    main()
