#!/usr/bin/env python3
"""Publish allowlisted metrics for the complete ordinary RAG control."""

import argparse
from collections import Counter
import json
from pathlib import Path

from export_evidence import dump, stream_hash


LABELS = {"correct", "correct_refusal", "partial", "incorrect", "incorrect_refusal"}
BEHAVIORS = {"grounded": 1600, "no_answer": 300, "refusal": 100}
FLAGS = ("runtime_ok", "e2e_pass", "exact_source_recall_at_10")


def read(path):
    return json.loads(path.read_text())


def by_case(path):
    with path.open() as stream:
        rows = [json.loads(line) for line in stream]
    index = {r["case_id"]: r for r in rows}
    assert len(index) == len(rows) == 2000
    return index


def summarize(rows):
    labels = Counter(r["projection"]["label"] for r in rows)
    assert labels.keys() <= LABELS
    assert len({r["case_key"] for r in rows}) == len(rows) == 2000
    assert Counter(r["projection"]["expected_answer_type"] for r in rows) == BEHAVIORS
    strict = labels["correct"] + labels["correct_refusal"]
    metrics = {"strict": (strict, 2000), "strict_or_partial": (strict + labels["partial"], 2000)}
    for key in FLAGS:
        metric = "e2e" if key == "e2e_pass" else key
        subset = [r["projection"] for r in rows if "recall" not in key
                  or r["projection"]["expected_answer_type"] == "grounded"]
        metrics[metric] = (sum(r[key] is True for r in subset), len(subset))
    return dict(labels), {k: dict(count=n, total=d) for k, (n, d) in metrics.items()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("evidence"))
    args = parser.parse_args()
    root = args.archive
    verification = read(root / "comparison/verified-evidence.json")
    for rel, sha in verification["sha256"].items():
        assert stream_hash(args.archive / rel) == sha
    identity = verification["identity"]
    assert identity["judge_model"] == "gpt-5.6-sol" and identity["judge_effort"] == "high"
    assert verification["judge_status"] == {"error": 0, "uncertain": 0, "runtime_skipped_count": 0}
    published = args.output / "proposed-system-evaluation"
    assert read(published / "summary.json")["provenance"]["cohort_manifest_sha256"] == (
        identity["inputs_sha256"]["cohort_manifest.json"]
    )
    reference = read(published / "case-labels.json")["rows"]
    by_question = {r["projection"]["question_sha256"]: r["case_key"] for r in reference}
    assert len(by_question) == 2000
    judge = by_case(root / "judge/semantic_judgments.jsonl")
    evaluation = by_case(root / "evaluation/judgments.jsonl")
    rows = []
    for case, receipt in judge.items():
        item = evaluation[case]["judgment"]
        assert receipt["evaluator_status"] == "ok" and receipt["label"] == item["semantic_judge_label"]
        projection = {"label": receipt["label"], "expected_answer_type": item["expected_answer_type"]}
        assert all(type(item[k]) is bool for k in FLAGS if item[k] is not None)
        projection.update({k: item[k] is True for k in FLAGS})
        rows.append({"case_key": by_question[receipt["question_sha256"]], "projection": projection})
    labels, metrics = summarize(rows)
    comparison = read(root / "comparison/comparison.json")
    assert labels == comparison["baseline"]["labels"]
    assert all(comparison["baseline"][k] == v for k, v in metrics.items() if k != "runtime_ok")
    assert metrics["runtime_ok"]["count"] == 2000
    out = args.output / "baseline-system-evaluation"
    dump(out / "case-labels.json", {"rows": sorted(rows, key=lambda r: r["case_key"])})
    dump(out / "summary.json", {
        "scope": "v1660_parameter_aligned_conventional_rag_control_same_development_cohort",
        "answer_model": "gpt-5.6-terra", "answer_reasoning_effort": "high",
        "judge_model": identity["judge_model"], "judge_reasoning_effort": identity["judge_effort"],
        "judge_contract": identity["judge_contract"],
        "cohort_manifest_sha256": identity["inputs_sha256"]["cohort_manifest.json"],
        "runtime_results_sha256": identity["runtime_results_sha256"],
        "index_manifest_sha256": identity["index_manifest_sha256"],
        "total": 2000, "recomputed_labels": labels, "metrics": metrics,
        "prompt_visible_context": {"field": "retriever_resources", "min": 0, "max": 16},
        "candidate_trace_depth": 100,
        "judge_errors": 0, "judge_skips": 0,
        "paired_deltas": comparison["descriptive_paired_deltas"],
    })


if __name__ == "__main__":
    main()
