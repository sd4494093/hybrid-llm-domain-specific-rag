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


if __name__ == "__main__":
    main()
