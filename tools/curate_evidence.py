#!/usr/bin/env python3
"""Build reviewer-readable projections and recompute verified result anchors."""

import argparse
import collections
import gzip
import json
from pathlib import Path

from export_evidence import digest, dump, project


BASELINE = ".ralph/runtime/prod_dual_region_1000q_semantic_oracle_20260605T072539HKT"
FINAL = ".playwright/v1660-relationship-source-order-20260906/full2000"


def rows(path):
    with (gzip.open(path, "rt") if path.suffix == ".gz" else path.open()) as stream:
        for line in stream:
            if line.strip():
                yield json.loads(line)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--output", type=Path, default=Path("evidence"))
    args = p.parse_args()
    source, out = args.source.resolve(), args.output.resolve()
    artifacts = {r["artifact_id"]: r for r in rows(out / "inventory.jsonl.gz")}

    def bound(rel):
        data = (source / rel).read_bytes()
        aid = digest(rel.encode())
        sha = digest(data)
        assert artifacts[aid]["source_sha256"] == sha, "Source changed since inventory"
        return {"artifact_id": aid, "source_sha256": sha}, json.loads(data)

    def cases(rel, output, semantic_key=None):
        aid = digest(rel.encode())
        sha = digest((source / rel).read_bytes())
        assert artifacts[aid]["source_sha256"] == sha
        result = []
        for row in rows(source / rel):
            identifier = next((row[k] for k in ("case_id", "question_id", "qid", "id") if k in row), None)
            assert identifier is not None
            identity = json.dumps([row.get("region"), identifier], sort_keys=True)
            safe = project(row)
            if semantic_key:
                label = row[semantic_key]
                assert label in {"correct", "partial", "incorrect", "refusal", "correct_refusal", "incorrect_refusal", "judge_error"}
                safe["label"] = label
            result.append({"case_key": digest(identity.encode()), "projection": safe})
        assert len({r["case_key"] for r in result}) == len(result)
        dump(output, {"source": {"artifact_id": aid, "source_sha256": sha}, "rows": result})
        return result

    summaries = {r["artifact_id"]: r for r in rows(out / "summaries.jsonl.gz")}
    for aid, row in summaries.items():
        dump(out / "summaries" / f"{aid}.json", row)
    for version in range(1, 1661):
        record = json.loads((out / "iterations" / f"v{version:04d}.json").read_text())
        path = out / "iteration-milestones" / f"v{version:04d}"
        path.mkdir(parents=True, exist_ok=True)
        related = [summaries[k] for k in record["summary_ids"]]
        dump(path / "summary.json", {"version": f"v{version}", "coverage": record["coverage"],
                                     "association": "path_mentions_not_verified_execution_identity",
                                     "summary_artifact_ids": record["summary_ids"]})
        lines = [f"# v{version}: Located Evidence", "",
                 f"Coverage: `{record['coverage']}`. This version has {len(record['artifact_ids'])} path-associated artifacts, "
                 f"{len(record['document_events'])} document references, and {len(record['commit_ids'])} commit-subject references.", "",
                 "Path mentions can identify a comparator, schema or question-set revision. They are not proof of a tested implementation.", "",
                 f"[Reference IDs](../../iterations/v{version:04d}.json) | [Full history](../../ITERATION_HISTORY.md)", "",
                 "| Artifact | Cases or rows | Status | Semantic numerator/denominator | E2E pass |", "|---|---:|---|---|---|"]
        for item in related:
            s = item["projection"]
            metric = s.get("quality_metrics", {}).get("semantic_correctness_rate", {})
            sem = f"{metric['numerator']}/{metric['denominator']}" if "numerator" in metric else "unreported"
            count = s.get("question_count", s.get("total_rows", s.get("total", "unreported")))
            lines.append(f"| [{item['artifact_id'][:12]}](../../summaries/{item['artifact_id']}.json) | {count} | {s.get('status', 'unreported')} | {sem} | {s.get('e2e_pass_count', 'unreported')} |")
        if not related:
            lines.extend(["", "No structured summary located by version-associated path. Consult document events and commit references; no score is inferred."])
        (path / "README.md").write_text("\n".join(lines) + "\n")

    # Bind the original and the resolved baseline rather than overwriting history.
    baseline_dir = out / "baseline-system-evaluation"
    initial_ref, initial = bound(BASELINE + "/full_semantic_judge/semantic_judge_summary.json")
    final_ref, baseline = bound(BASELINE + "/full_semantic_judge_combined/semantic_judge_summary.json")
    baseline_rows = cases(BASELINE + "/full_semantic_judge_combined/semantic_judge_results.jsonl", baseline_dir / "case-labels.json", "semantic_label")
    labels = dict(collections.Counter(r["projection"]["label"] for r in baseline_rows))
    assert labels == baseline["by_label"] and len(baseline_rows) == baseline["total_rows"] == 2000
    dump(baseline_dir / "initial-summary.json", {"source": initial_ref, "projection": project(initial)})
    dump(baseline_dir / "summary.json", {"scope": "historical_MVP_UAT_aggregated_2000_runs", "source": final_ref,
         "projection": project(baseline), "recomputed_labels": labels, "total": 2000,
         "strict_correctness": {"numerator": labels["correct"], "denominator": 2000, "rate": labels["correct"] / 2000},
         "usefulness": {"numerator": labels["correct"] + labels["partial"], "denominator": 2000, "rate": (labels["correct"] + labels["partial"]) / 2000},
         "judge_model_observed": "gpt-5.5",
         "retry_resolution": {"initial_judge_errors": initial["judge_error_rows"], "combined_judge_errors": baseline["judge_error_rows"], "combined_retry_rows": baseline["retry_rows"]},
         "comparison_limit": "Different cohort and evaluator from September natural-user evaluation; sample-size equality is not protocol equivalence."})

    final_dir = out / "proposed-system-evaluation"
    sources = {}
    for alias, rel in {"evaluation": "/evaluation-complete/summary.json", "judge": "/judge-complete/summary.json",
                       "failure-cohort": "/failure-cohort/summary.json", "promotion": "/baseline-decision.json"}.items():
        ref, data = bound(FINAL + rel)
        sources[alias] = {"source": ref, "projection": project(data)}
        dump(final_dir / f"{alias}.json", sources[alias])
    judges = cases(FINAL + "/judge-complete/semantic_judgments.jsonl", final_dir / "case-labels.json", "label")
    evaluated = cases(FINAL + "/evaluation-complete/judgments.jsonl", final_dir / "case-evaluation.json")
    labels = dict(collections.Counter(r["projection"]["label"] for r in judges))
    ev = sources["evaluation"]["projection"]
    assert len(judges) == len(evaluated) == 2000
    assert labels == {"correct": 1055, "correct_refusal": 396, "partial": 354, "incorrect": 91, "incorrect_refusal": 104}
    assert sum(r["projection"]["judgment"]["e2e_pass"] for r in evaluated) == ev["e2e_pass_count"] == 1422
    assert labels["correct"] + labels["correct_refusal"] == ev["quality_metrics"]["semantic_correctness_rate"]["numerator"] == 1451
    dump(final_dir / "summary.json", {"scope": "local_dev_natural_user_v1660", "version": "v1660",
         "sources": {k: v["source"] for k, v in sources.items()}, "total": 2000,
         "answer_model": "gpt-5.6-terra", "answer_reasoning_effort": "high",
         "judge_model": ev["semantic_judge_model"], "judge_reasoning_effort": ev["semantic_judge_reasoning_effort"],
         "recomputed_labels": labels, "quality_metrics": ev["quality_metrics"],
         "e2e_pass_count": ev["e2e_pass_count"], "e2e_pass_rate": ev["e2e_pass_rate"], "failure_classes": ev["failure_classes"],
         "semantic_failure_count": 549, "e2e_failure_count": 578,
         "failure_cohort_buckets": sources["failure-cohort"]["projection"]["failure_buckets"],
         "quality_gate": ev["quality_gate"],
         "first_attempt_success_count": ev["first_attempt_success_count"],
         "recovered_after_retry_count": ev["recovered_after_retry_count"],
         "unrecovered_transport_failure_count": ev["unrecovered_transport_failure_count"],
         "semantic_judge_error_count": ev["semantic_judge_error_count"], "semantic_judge_uncertain_count": ev["semantic_judge_uncertain_count"],
         "provenance": {k: ev[k] for k in ("questions_sha256", "oracles_sha256", "source_snapshot_id", "run_provenance_sha256", "cohort_manifest_sha256")},
         "interpretation": "Strict semantic correctness includes correct refusals. Original automated labels and ownership buckets are preserved here. See paper-reporting.json for the paper definition: 411 planner/prefill recovery cases are partially correct, yielding 1862/2000 correct-or-partial usefulness. No production-acceptance claim."})

    # Add human-readable observed full-cohort summaries without selecting the maximum.
    lines = ["# Full-Cohort Evaluation Inventory", "", "All discovered 2,000-case evaluation summaries are retained, including intermediate and rejected results.", "",
             "Version association is derived from source paths. Match provenance and acceptance evidence before comparing rows.", "",
             "| Referenced versions | Artifact | Semantic correct / total | E2E pass | Judge errors | Judge uncertain |", "|---|---|---|---|---|---|"]
    for row in json.loads((out / "full-cohort-summary-candidates.json").read_text()):
        s = row["projection"]
        m = s["quality_metrics"]["semantic_correctness_rate"]
        lines.append(f"| {', '.join('v' + str(v) for v in row['version_mentions']) or 'unattributed'} | [{row['artifact_id'][:12]}](summaries/{row['artifact_id']}.json) | {m['numerator']}/{m['denominator']} | {s.get('e2e_pass_count', 'unreported')} | {s.get('semantic_judge_error_count', 'unreported')} | {s.get('semantic_judge_uncertain_count', 'unreported')} |")
    (out / "FULL_COHORT_EVALUATIONS.md").write_text("\n".join(lines) + "\n")
    # Make each version table link directly to a readable report.
    for page in (out / "history").glob("*.md"):
        text = page.read_text()
        for v in range(1, 1661):
            text = text.replace(f"../iterations/v{v:04d}.json", f"../iteration-milestones/v{v:04d}/README.md")
        page.write_text(text)
    print(json.dumps({"reviewer_summaries": len(summaries), "version_reports": 1660, "baseline_labels": baseline["by_label"], "v1660_labels": labels}, indent=2))


if __name__ == "__main__":
    main()
