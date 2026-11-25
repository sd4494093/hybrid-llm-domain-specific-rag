#!/usr/bin/env python3
"""Export bounded, content-free support for the manuscript's feedback cases."""

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess

from export_evidence import dump


def sha(data):
    return hashlib.sha256(data).hexdigest()


def case_key(row):
    return sha(json.dumps([row.get("region"), row["case_id"]], sort_keys=True).encode())


class Sources:
    def __init__(self, root, inventory):
        self.root = root.resolve()
        self.inventory = inventory
        self.inputs = {}
        self.objects = {}

    def read(self, relative, jsonl=False, text=False):
        path = (self.root / relative).resolve()
        assert path.is_relative_to(self.root), "Input escapes source repository"
        raw = path.read_bytes()
        identifier = sha(path.relative_to(self.root).as_posix().encode())
        item = {"input_id": identifier, "source_sha256": sha(raw), "bytes": len(raw)}
        if identifier in self.inventory:
            assert self.inventory[identifier]["source_sha256"] == item["source_sha256"]
            item["inventory_artifact_id"] = identifier
        self.inputs[identifier] = item
        if text:
            return raw.decode()
        if jsonl:
            return [json.loads(line) for line in raw.splitlines() if line.strip()]
        return json.loads(raw)

    def git_object(self, specification):
        raw = subprocess.check_output(["git", "-C", str(self.root), "show", specification])
        identifier = sha(specification.encode())
        self.objects[identifier] = {"object_id": identifier, "commit": specification.split(":")[0],
                                    "source_sha256": sha(raw), "bytes": len(raw)}
        return raw.decode()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    args = parser.parse_args()
    public = Path(__file__).resolve().parents[1] / "evidence"
    import gzip
    with gzip.open(public / "inventory.jsonl.gz", "rt") as stream:
        inventory = {row["artifact_id"]: row for row in map(json.loads, stream)}
    source = Sources(args.source, inventory)
    out = public / "audit-feedback"
    base = "tests/e2e/e2e_20260721_dev_gold/agents_evidence/natural_user_gold/"
    final = ".playwright/v1660-relationship-source-order-20260906/"
    last = source.read(final + "full2000/judge-complete/semantic_judgments.jsonl", jsonl=True)
    by_id = {row["case_id"]: row for row in last}
    assert len(last) == len(by_id) == 2000
    published = json.loads((public / "proposed-system-evaluation/case-labels.json").read_text())
    public_rows = {row["case_key"]: row["projection"] for row in published["rows"]}
    for row in last:
        assert public_rows[case_key(row)]["answer_sha256"] == row["answer_sha256"]
        assert public_rows[case_key(row)]["label"] == row["label"]
    buckets = source.read(final + "full2000/failure-cohort/failure_buckets.json")
    membership = {identifier: bucket for bucket, identifiers in buckets.items() for identifier in identifiers}
    assert len(membership) == sum(map(len, buckets.values())) == 549
    crosswalk = {bucket: dict(Counter(by_id[i]["label"] for i in identifiers))
                 for bucket, identifiers in buckets.items()}
    dump(out / "ownership-crosswalk.json", {
        "label_counts": dict(Counter(row["label"] for row in last)), "crosswalk": crosswalk,
        "rows": [{"case_key": case_key(by_id[i]), "answer_sha256": by_id[i]["answer_sha256"],
                  "original_judge_label": by_id[i]["label"], "ownership": bucket}
                 for i, bucket in sorted(membership.items())], "new_semantic_grading": False})

    recovery = "tmp/E2E_20260603_V2_Test/06_qualification/"
    qualification = source.read(recovery + "qualification_summary.json")
    rule = source.read(recovery + "rule_retest_execution_aggregate_summary.json")
    assessment = source.read(recovery + "ai_second_check_aggregate_summary.json")
    chunks = source.read(recovery + "chunk_execution_aggregate_summary.json")
    ingestion = source.read(recovery + "dify_ingest_aggregate_summary.json")
    snapshot = source.read(".agent_discussion/evidence/20260603_sg_ingestion_source_vs_vector_reconciliation.md", text=True)
    for status, count in [("ingested", 8358), ("ai_rejected", 957), ("needs_review", 375),
                          ("ingest_failed", 335), ("rule_failed", 136)]:
        line, = [line for line in snapshot.splitlines() if line.startswith(f"| `{status}` |")]
        assert f"{count:,}" in line or str(count) in line
    assert set(rule["transitioned_ids"]) == set(assessment["transitioned_ids"])
    assert len(set(rule["transitioned_ids"])) == 115
    assert assessment["verdict_counts"] == {"pass": 111, "reject": 2, "needs_review": 2}
    assert set(chunks["ids"]) == set(ingestion["ids"])
    assert len(set(chunks["ids"])) == 111
    assert set(chunks["ids"]) <= set(rule["transitioned_ids"])
    document_keys = lambda ids: sorted(sha(f"staging-document:{i}".encode()) for i in ids)
    corpus = source.read("tests/e2e/e2e_20260721_dev_gold/agents_evidence/closure/local_dev_gold_summary.json")["corpus"]
    dump(out / "admission-recovery.json", {
        "initial_status_counts": {"ingested": 8358, "ai_rejected": 957, "needs_review": 375,
                                  "ingest_failed": 335, "rule_failed": 136},
        "qualification_groups": {prefix.rstrip("_"): sum(n for k, n in qualification["decision_counts"].items()
                                  if k.startswith(prefix))
                                 for prefix in ["keep_excluded_", "candidate_", "payload_unresolved_"]},
        "model_verdicts": assessment["verdict_counts"], "rule_passed": 115,
        "subsequently_ingested": 111, "staging_chunks": chunks["total_chunks_written"],
        "maximum_staging_chunk_tokens": chunks["max_token_count"],
        "rule_passed_document_keys": document_keys(rule["transitioned_ids"]),
        "chunked_document_keys": document_keys(chunks["ids"]),
        "ingested_document_keys": document_keys(ingestion["ids"]),
        "later_staging_status_counts": {key: corpus[key] for key in
            ["ingested", "ai_rejected", "needs_review", "rule_failed", "rule_passed", "ingest_failed"]},
        "later_ingested_increase": corpus["ingested"] - 8358,
        "outside_traced_recovery_cohort": corpus["ingested"] - 8358 - 111,
        "independent_document_quality_annotation": False,
        "all_later_documents_have_individually_verified_two_gate_history": False})

    retrieval = base + "rca/v241_natural_user_gold_2000_final_retrieval_rca_20260727/"
    diagnostic = source.read(retrieval + "summary.json")
    diagnostic_rows = source.read(retrieval + "cases.safe.jsonl", jsonl=True)
    assert dict(Counter(row["miss_class"] for row in diagnostic_rows)) == diagnostic["miss_class_counts"]
    dump(out / "retrieval-diagnosis.json", {
        "version": "v241", "grounded_cases": diagnostic["grounded_case_count"],
        "miss_class_counts": diagnostic["miss_class_counts"],
        "rows": [{"case_key": case_key(row), "miss_class": row["miss_class"]} for row in diagnostic_rows]})

    fact_outputs = {}
    for name, folder in [("original", "rca-context-facts-12"), ("replay", "rca-context-facts-12-replay")]:
        summary = source.read(final + folder + "/summary.json")
        rows = source.read(final + folder + "/cases.safe.jsonl", jsonl=True)
        assert len(rows) == summary["case_count"] == 12
        for field in ["required_fact_count", "context_supported_fact_count", "answer_covered_fact_count"]:
            assert sum(row[field] for row in rows) == summary[field]
        safe = [{"case_key": case_key(by_id[row["case_id"]]), **{key: row[key] for key in
                ["answer_sha256", "runtime_context_sha256", "oracle_facts_sha256", "owner_signal",
                 "required_fact_count", "context_supported_fact_count", "answer_covered_fact_count"]}}
                for row in rows]
        fact_outputs[name] = {"rows": safe, "case_count": summary["case_count"],
                              **{key: summary[key] for key in ["required_fact_count", "context_supported_fact_count",
                                  "answer_covered_fact_count", "owner_signal_counts"]}}
    originals = {row["case_key"]: row for row in fact_outputs["original"]["rows"]}
    replays = {row["case_key"]: row for row in fact_outputs["replay"]["rows"]}
    assert originals.keys() == replays.keys()
    assert all(public_rows[key]["answer_sha256"] == row["answer_sha256"] for key, row in originals.items())
    fact_outputs["answers_changed_on_replay"] = sum(originals[k]["answer_sha256"] != replays[k]["answer_sha256"] for k in originals)
    assert fact_outputs["answers_changed_on_replay"] == 11
    fact_outputs["replay_is_regrading_of_original_answers"] = False
    dump(out / "fact-coverage.json", fact_outputs)

    analyses = base + "analysis/"
    locations = {"v1222": "v1222_full_2000q_20260814/parallel_natural_gold_20260814T082559Z",
                 "v1225": "v1225_full_2000q_20260815/parallel_natural_gold_20260814T203406Z",
                 "v1226": "v1226_full_2000q_20260815/parallel_natural_gold_20260815T073240Z",
                 "v1227": "v1227_full_2000q_20260816/parallel_natural_gold_20260816T092214Z",
                 "v1371": "v1408_full_2000q_v1371_20260823/parallel_natural_gold_20260823T003701Z"}
    provenances = {v: source.read(analyses + path + "/provenance.json") for v, path in locations.items()}
    provenances["v1660"] = source.read(final + "full2000/runtime/parallel_natural_gold_20260905T162455Z/provenance.json")
    settings = {}
    for version, provenance in provenances.items():
        runtime = provenance["runtime_contract"]
        settings[version] = {"question_revision": "v19" if version in {"v1371", "v1660"} else "v4",
            "source_snapshot_id": provenance["source_snapshot_id"],
            "questions_sha256": provenance["questions_sha256"],
            "runtime_state_sha256": provenance["dataset_runtime_snapshot_sha256"],
            "runtime_state": {key: provenance["dataset_runtime_snapshot"][key] for key in
                 ["document_count", "segment_count", "active_completed_document_count", "active_completed_segment_count"]},
            "serving": {key: runtime.get(key) for key in
                 ["top_k", "rerank_mode", "rerank_model", "reasoning_effort", "vector_weight", "keyword_weight",
                  "final_answer_model", "final_answer_reasoning_effort"]}}
    dump(out / "run-settings.json", settings)

    before_path = analyses + "v1441_terra_high_parallel4_full_2000q_20260828/strict_runtime/parallel_natural_gold_20260828T002047Z/"
    before = source.read(before_path + "evaluation/semantic_judge_merged_retry_20260904_primary_degraded/semantic_judgments.jsonl", jsonl=True)
    before_summary = source.read(before_path + "evaluation_merged_retry_20260904_primary_degraded/summary.json")
    before_map = {row["case_id"]: row for row in before}
    assert len(before_map) == 2000 and before_map.keys() == by_id.keys()
    assert all(before_map[key]["question_sha256"] == by_id[key]["question_sha256"] for key in by_id)
    strict = {"correct", "correct_refusal"}
    paired = [{"case_key": case_key(by_id[key]), "before_label": before_map[key]["label"],
               "after_label": by_id[key]["label"], "question_sha256": by_id[key]["question_sha256"]}
              for key in sorted(by_id)]
    lost = sum(row["before_label"] in strict and row["after_label"] not in strict for row in paired)
    gained = sum(row["before_label"] not in strict and row["after_label"] in strict for row in paired)
    assert (lost, gained) == (119, 135)
    assert sum(row["label"] in strict for row in before) == before_summary["quality_metrics"]["semantic_correctness_rate"]["numerator"] == 1435
    decisions = [source.read(final + "full2000/" + file) for file in ["baseline-decision.json", "baseline-decision-final.json"]]
    assert decisions[0]["decision"] == "PROMOTE_CANDIDATE" and decisions[0]["delta_correct"] == 16
    assert decisions[1]["decision"] == "RESTORE_ACCEPTED_BASELINE" and decisions[1]["delta_correct"] == 0
    assert all(decisions[0][key] == decisions[1][key] for key in ["candidate_summary_sha256", "candidate_provenance_sha256"])
    implementation = source.read("scripts/local_dev/gate_natural_user_full_baseline.py", text=True)
    assert "improved = candidate_count > baseline_count" in implementation
    dump(out / "promotion-decisions.json", {
        "strict_count_before": 1435, "strict_count_after": 1451, "strict_lost": lost, "strict_gained": gained,
        "paired_rows": paired, "promotion_rule": "strict_count_increase_after_identity_checks",
        "focused_tests_can_promote": False,
        "decisions": [{key: row[key] for key in ["decision", "baseline_semantic_correct_count",
            "candidate_semantic_correct_count", "delta_correct", "strict_monotonic_improvement_required",
            "candidate_summary_sha256", "candidate_provenance_sha256"]} for row in decisions],
        "second_decision_is_same_candidate_self_comparison": True,
        "second_decision_proves_distinct_candidate_rollback": False})

    regress = base + "evaluation/v700_v694_v699_regression17_20260806/"
    local_decision = source.read(regress + "decision.md", text=True)
    assert "Decision: accept" in local_decision and "not a formal 200Q or 2000Q" in local_decision
    local_summary = source.read(regress + "summary.json")
    local_judgments = source.read(base + "semantic/v699_v698_v697_merged_final_20260806/semantic_judgments.jsonl", jsonl=True)
    controls = source.read(base + "semantic/v692_v691_v690_troubleshooting_controls3_20260806/semantic_judgments.jsonl", jsonl=True)
    previous = source.read(base + "semantic/v688_v687_v686_regression17_20260806/semantic_judgments.jsonl", jsonl=True)
    target = "NATURAL-0025"
    previous_row, = [row for row in previous if row["case_id"] == target]
    final_row, = [row for row in local_judgments if row["case_id"] == target]
    assert previous_row["question_sha256"] == final_row["question_sha256"]
    assert previous_row["label"] == "incorrect" and final_row["label"] == "correct"
    assert Counter(row["label"] for row in local_judgments) == {"correct": 15, "partial": 2}
    assert len(controls) == 3 and all(row["label"] == "correct" for row in controls)
    runtime = source.read(base + "runtime/v694_v690_regression17_retry2_20260806/20260805T180752+0000/results.jsonl", jsonl=True)
    runtime_row, = [row for row in runtime if row["case_id"] == target]
    repairs = [repair for resource in runtime_row["retriever_resources"]
               for key, debug in resource.get("metadata", {}).items()
               if key.endswith("selection_debug") and isinstance(debug, dict)
               for repair in debug.get("troubleshooting_section_repairs", [])]
    repair = {key: repairs[0][key] for key in ["anchor_position", "continuation_position", "replaced_position"]}
    assert repair == {"anchor_position": 18, "continuation_position": 19, "replaced_position": 11}
    later = source.read(base + "evaluation/v705_v701_v704_scale200_20260806/summary.json")
    patch_commit = "995223b676fd82a68e2cae363b28c56f29ad761d"
    patch = source.git_object(patch_commit)
    assert "troubleshooting_section" in patch
    rejected = source.read(".playwright/v1647-hydrated-context-sibling-rerank-20260905/natural-0460-admission/admission_verdict.json")
    revert_commit = "a4041d5f61f80d7dae7565c040b0c605346b6cbf"
    revert = source.git_object(revert_commit)
    assert "14aa3442127bcc2ea6bc23562a40584eae2c3a5e" in revert
    assert rejected["verdict"] == "REJECT" and not rejected["runtime"]["expected_parent_selected"]
    dump(out / "completed-cycles.json", {
        "context_continuity": {"target_case_key": case_key(final_row), "before_label": previous_row["label"],
            "after_label": final_row["label"], "repair_positions": repair,
            "controls": {"cases": 3, "correct": 3}, "regression_labels": dict(Counter(row["label"] for row in local_judgments)),
            "first_attempt_success_count": local_summary["first_attempt_success_count"],
            "decision": "accepted_for_local_continuation", "change_commit": patch_commit,
            "later_cohort": {"cases": later["question_count"],
                "strict_correct": later["quality_metrics"]["semantic_correctness_rate"]["numerator"],
                "quality_gate": later["quality_gate"]["status"]}},
        "hydrated_sibling_rerank": {"decision": rejected["verdict"], "owning_layer": rejected["owning_layer"],
            "before_expected_parent_selected": rejected["baseline_comparison"]["expected_parent_selected"],
            "after_expected_parent_selected": rejected["runtime"]["expected_parent_selected"],
            "before_label": rejected["baseline_comparison"]["semantic_label"],
            "after_label": rejected["semantic_judge"]["label"],
            "before_score": rejected["baseline_comparison"]["semantic_score_0_5"],
            "after_score": rejected["semantic_judge"]["score_0_5"], "revert_commit": revert_commit},
        "answer_audit_triggered_rechunking_demonstrated": False,
        "full_final_cohort_online_verifier_intervention_counts_available": False})
    outputs = {path.name: {"sha256": sha(path.read_bytes()), "bytes": path.stat().st_size}
               for path in sorted(out.glob("*.json")) if path.name != "input-provenance.json"}
    dump(out / "input-provenance.json", {"schema_version": 1, "inputs": sorted(source.inputs.values(), key=lambda x: x["input_id"]),
        "git_objects": sorted(source.objects.values(), key=lambda x: x["object_id"]),
        "outputs": outputs,
        "private_source_content_exported": False, "new_rag_experiment": False, "new_semantic_grading": False})
    print(json.dumps({"status": "PASS", "inputs_bound": len(source.inputs), "git_objects_bound": len(source.objects)}, indent=2))


if __name__ == "__main__":
    main()
