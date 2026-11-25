#!/usr/bin/env python3
"""Recount the sanitized feedback supplement without access to private content."""

from collections import Counter
import gzip
import hashlib
import json
from math import comb
from pathlib import Path
import re


HEX = re.compile(r"[a-f0-9]{64}")


def exact_paired_p(lost, gained):
    n = lost + gained
    return min(1.0, 2 * sum(comb(n, k) for k in range(min(lost, gained) + 1)) / 2 ** n)


def verify(folder, public_rows, inventory=None):
    def load(name):
        return json.loads((folder / (name + ".json")).read_text())

    provenance = load("input-provenance")
    assert provenance["private_source_content_exported"] is False
    assert provenance["new_rag_experiment"] is False and provenance["new_semantic_grading"] is False
    assert len({item["input_id"] for item in provenance["inputs"]}) == len(provenance["inputs"])
    for item in provenance["inputs"]:
        assert HEX.fullmatch(item["input_id"]) and HEX.fullmatch(item["source_sha256"])
        if inventory is not None and "inventory_artifact_id" in item:
            assert inventory[item["inventory_artifact_id"]]["source_sha256"] == item["source_sha256"]
    for name, fingerprint in provenance["outputs"].items():
        assert Path(name).name == name
        raw = (folder / name).read_bytes()
        assert len(raw) == fingerprint["bytes"] and hashlib.sha256(raw).hexdigest() == fingerprint["sha256"]

    ownership = load("ownership-crosswalk")
    rows = ownership["rows"]
    assert len({row["case_key"] for row in rows}) == len(rows) == 549
    crosswalk = {}
    for row in rows:
        public = public_rows[row["case_key"]]
        assert public["label"] == row["original_judge_label"]
        assert public["answer_sha256"] == row["answer_sha256"]
        crosswalk.setdefault(row["ownership"], Counter())[row["original_judge_label"]] += 1
    assert {key: dict(value) for key, value in crosswalk.items()} == ownership["crosswalk"]
    assert dict(Counter(row["label"] for row in public_rows.values())) == ownership["label_counts"]
    assert crosswalk["planner/partial"] == {"partial": 340, "incorrect": 71}
    assert crosswalk["citation/source"]["partial"] == 14
    assert ownership["label_counts"]["partial"] == 354

    admission = load("admission-recovery")
    assert sum(admission["initial_status_counts"].values()) == 10161
    assert sum(admission["qualification_groups"].values()) == 1803
    assert admission["model_verdicts"] == {"pass": 111, "reject": 2, "needs_review": 2}
    assert len(set(admission["rule_passed_document_keys"])) == admission["rule_passed"] == 115
    assert admission["ingested_document_keys"] == admission["chunked_document_keys"]
    assert len(set(admission["ingested_document_keys"])) == admission["subsequently_ingested"] == 111
    assert set(admission["ingested_document_keys"]) <= set(admission["rule_passed_document_keys"])
    assert admission["later_ingested_increase"] == 389 and admission["outside_traced_recovery_cohort"] == 278

    retrieval = load("retrieval-diagnosis")
    assert dict(Counter(row["miss_class"] for row in retrieval["rows"])) == retrieval["miss_class_counts"]
    assert len(retrieval["rows"]) == retrieval["grounded_cases"] == 1600
    assert retrieval["miss_class_counts"] == {"exact_source_hit_at_10": 564,
        "expected_candidate_not_selected": 432, "expected_not_in_candidate_set": 604}

    facts = load("fact-coverage")
    groups = {}
    for name in ["original", "replay"]:
        group = facts[name]
        groups[name] = {row["case_key"]: row for row in group["rows"]}
        assert len(groups[name]) == group["case_count"] == 12
        for field in ["required_fact_count", "context_supported_fact_count", "answer_covered_fact_count"]:
            assert sum(row[field] for row in group["rows"]) == group[field]
        assert dict(Counter(row["owner_signal"] for row in group["rows"])) == group["owner_signal_counts"]
    assert groups["original"].keys() == groups["replay"].keys()
    assert all(public_rows[key]["answer_sha256"] == row["answer_sha256"] and public_rows[key]["label"] == "partial"
               for key, row in groups["original"].items())
    changed = sum(groups["original"][key]["answer_sha256"] != groups["replay"][key]["answer_sha256"]
                  for key in groups["original"])
    assert changed == facts["answers_changed_on_replay"] == 11
    assert facts["replay_is_regrading_of_original_answers"] is False

    settings = load("run-settings")
    assert len({run["source_snapshot_id"] for run in settings.values()}) == 1
    assert len({settings[v]["runtime_state_sha256"] for v in ["v1222", "v1225", "v1226", "v1227"]}) == 1
    assert settings["v1371"]["runtime_state_sha256"] == settings["v1660"]["runtime_state_sha256"]
    assert settings["v1660"]["serving"]["vector_weight"] == 0.65
    assert settings["v1660"]["serving"]["keyword_weight"] == 0.35
    assert settings["v1660"]["serving"]["final_answer_model"] == "gpt-5.6-terra"

    promotion = load("promotion-decisions")
    paired = promotion["paired_rows"]
    assert len({row["case_key"] for row in paired}) == len(paired) == 2000
    strict = {"correct", "correct_refusal"}
    lost = gained = 0
    for row in paired:
        assert public_rows[row["case_key"]]["label"] == row["after_label"]
        assert public_rows[row["case_key"]]["question_sha256"] == row["question_sha256"]
        lost += row["before_label"] in strict and row["after_label"] not in strict
        gained += row["before_label"] not in strict and row["after_label"] in strict
    assert (lost, gained) == (promotion["strict_lost"], promotion["strict_gained"]) == (119, 135)
    before = sum(row["before_label"] in strict for row in paired)
    after = sum(row["after_label"] in strict for row in paired)
    assert (before, after) == (promotion["strict_count_before"], promotion["strict_count_after"]) == (1435, 1451)
    assert after - before == gained - lost == 16
    first, second = promotion["decisions"]
    assert first["decision"] == "PROMOTE_CANDIDATE" and first["delta_correct"] == 16
    assert second["decision"] == "RESTORE_ACCEPTED_BASELINE" and second["delta_correct"] == 0
    assert all(first[key] == second[key] for key in ["candidate_summary_sha256", "candidate_provenance_sha256"])
    assert promotion["second_decision_proves_distinct_candidate_rollback"] is False

    cycles = load("completed-cycles")
    repair = cycles["context_continuity"]
    assert repair["before_label"] == "incorrect" and repair["after_label"] == "correct"
    assert repair["regression_labels"] == {"correct": 15, "partial": 2}
    assert repair["repair_positions"] == {"anchor_position": 18, "continuation_position": 19, "replaced_position": 11}
    assert repair["later_cohort"] == {"cases": 200, "strict_correct": 165, "quality_gate": "FAIL"}
    rejected = cycles["hydrated_sibling_rerank"]
    assert rejected["decision"] == "REJECT" and rejected["before_expected_parent_selected"] is True
    assert rejected["after_expected_parent_selected"] is False
    assert (rejected["before_score"], rejected["after_score"]) == (3, 2)
    return {"status": "PASS", "private_inputs_fingerprinted": len(provenance["inputs"]),
            "public_case_labels_joined": len(public_rows), "strict_lost": lost, "strict_gained": gained,
            "paired_exact_p": exact_paired_p(lost, gained), "replay_answers_changed": changed,
            "private_content_independently_reassessed": False}


def main():
    evidence = Path(__file__).resolve().parents[1] / "evidence"
    labels = json.loads((evidence / "proposed-system-evaluation/case-labels.json").read_text())
    public_rows = {row["case_key"]: row["projection"] for row in labels["rows"]}
    with gzip.open(evidence / "inventory.jsonl.gz", "rt") as stream:
        inventory = {row["artifact_id"]: row for row in map(json.loads, stream)}
    print(json.dumps(verify(evidence / "audit-feedback", public_rows, inventory), indent=2))


if __name__ == "__main__":
    main()
