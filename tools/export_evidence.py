#!/usr/bin/env python3
"""Export a conservative, content-free audit of a private experiment repository."""

import argparse
import collections
import contextlib
import gzip
import hashlib
import json
import math
import os
from pathlib import Path
import re
import subprocess


VERSION = re.compile(r"(?<![a-zA-Z0-9])v0*(\d{1,4})(?!\d)", re.I)
ROOTS = (".playwright", ".ralph", "tests/e2e", "tmp", "doc/dify_dev")
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv"}
LABELS = set("correct partial incorrect refusal correct_refusal incorrect_refusal judge_error error uncertain ok pass fail PASS FAIL SKIP HOLD_UNPROVEN NO_GO PROMOTE_CANDIDATE HOLD_BASELINE grounded no_answer supported unsupported fully_grounded partially_grounded not_grounded unknown true false high low medium question_only source_aware source_url_then_title runtime_error_or_timeout citation_wrong_source grounded_no_answer no_answer_incorrect semantic_incomplete semantic_incorrect semantic_judge_rejected semantic_judge_indeterminate runtime_skipped".split())
COUNTS = set("total total_rows judged_rows judge_error_rows correct_rows correct_or_partial_rows retry_rows question_count result_count error_count miss_count correct partial incorrect refusal correct_refusal incorrect_refusal judge_error error uncertain ok pass fail PASS FAIL count pass_count fail_count numerator denominator rate e2e_pass_count e2e_pass_rate first_attempt_success_count recovered_after_retry_count unrecovered_transport_failure_count indeterminate_count semantic_judge_error_count semantic_judge_uncertain_count failure_case_count sentinel_case_count selected_case_count delta_correct baseline_semantic_correct_count candidate_semantic_correct_count semantic_denominator acceptance_target_count replacement_count question_count result_count elapsed_seconds concurrency max_workers case_workers top_k recall_at_1 recall_at_3 recall_at_5 recall_at_10 strict_semantic_accuracy_rate useful_semantic_rate_correct_or_partial critical_severe_error_count grounded_count no_answer_count refusal_count row_count duplicate_case_id_count violation_count source_contract_count source_evidence_count negative_evidence_contract_count semantic_fact_count actual expected min max actual_numerator min_numerator attempts retry_count runtime_source_evidence_count score_0_5 latency_ms answer_url_count semantic_score semantic_score_rounded semantic_judge_material_error_count semantic_judge_unsupported_claim_count citation_wrong_source grounded_no_answer no_answer_incorrect semantic_incomplete semantic_incorrect semantic_judge_rejected semantic_judge_indeterminate runtime_error_or_timeout runtime_skipped".split())
BOOLS = set("e2e_pass semantic_pass runtime_ok citation_pass citation_support_pass critical_case deterministic_contract_pass deterministic_semantic_diagnostic_pass semantic_content_pass no_answer_detected retrieval_recall_at_10 retrieval_recall_at_30 exact_source_recall_at_10 exact_source_recall_at_30 contradiction candidate_improved candidate_meets_85_percent_target strict_monotonic_improvement_required focused_result_can_promote_baseline machine_semantic_judge_complete machine_semantic_judgments_present machine_semantic_judge_required pass".split())
ENUMS = set("status decision label semantic_label evaluator_status semantic_judge_label semantic_judge_status failure_class expected_answer_type groundedness citation_support semantic_judge_groundedness semantic_judge_citation_support semantic_judge_contradiction query_mode reasoning_effort semantic_judge_reasoning_effort retrieval_query_contract".split())
MODELS = {"gpt-5.5", "gpt-5.6-sol", "gpt-5.6-terra", "bge-m3"}
METRICS = set("semantic_correctness_rate critical_semantic_correctness_rate grounded_rate citation_support_correctness_rate retrieval_recall_at_10 correct_refusal_rate false_refusal_rate unsupported_assertion_rate contradiction_rate runtime_success_rate".split())
CONTAINERS = set("quality_metrics quality_gate checks expected_question_count semantic_correctness_rate integrity by_label failure_classes semantic_judge_status_counts judgment results summary statistics counts metrics runtime_statistics dimension_rates language domain answer_type failure_buckets source_failure_buckets".split()) | METRICS
DIMENSIONS = set("cs de en es fr it nl pl pt ro tr grounded no_answer refusal commercial_customer_marketing corporate_operations_policy_communications it_security_digital_workplace people_learning product_engineering safety_field_operations planner/partial no-answer citation/source".split())
HASH_FIELDS = set("questions_sha256 oracles_sha256 cohort_manifest_sha256 source_snapshot_id run_provenance_sha256 judgments_sha256 answer_sha256 question_sha256 reference_answer_sha256 oracle_facts_sha256 runtime_source_evidence_sha256 source_evidence_sha256 candidate_summary_sha256 candidate_provenance_sha256 model_config_sha256".split())


def digest(data):
    return hashlib.sha256(data).hexdigest()


def versions(text):
    return sorted({int(v) for v in VERSION.findall(text) if 1 <= int(v) <= 1660})


def project(value):
    """Allow named metrics and enums only; never copy arbitrary free text or keys."""
    if not isinstance(value, dict):
        return {}
    out = {}
    for key, item in value.items():
        if key in COUNTS | DIMENSIONS and type(item) in (int, float) and math.isfinite(item):
            out[key] = item
        elif key in BOOLS and type(item) is bool:
            out[key] = item
        elif key in ENUMS and isinstance(item, str) and item in LABELS:
            out[key] = item
        elif key in ("model", "semantic_judge_model") and isinstance(item, str) and item in MODELS:
            out[key] = item
        elif key in HASH_FIELDS and isinstance(item, str) and re.fullmatch(r"[a-f0-9]{64}", item):
            out[key] = item
        elif key in CONTAINERS | DIMENSIONS and isinstance(item, dict):
            child = project(item)
            if child:
                out[key] = child
    return out


def dump(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=True, sort_keys=True, indent=2) + "\n")


@contextlib.contextmanager
def compressed(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0, compresslevel=6) as stream:
            yield stream


def emit(stream, row):
    stream.write((json.dumps(row, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n").encode())


def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args], text=True)


def stream_hash(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("evidence"))
    args = parser.parse_args()
    root, out = args.source.resolve(), args.output.resolve()
    if out.is_relative_to(root):
        parser.error("Output must be outside the private source repository")
    out.mkdir(parents=True, exist_ok=True)
    records = {v: {"version": f"v{v}", "artifact_ids": [], "summary_ids": [],
                   "document_events": [], "commit_ids": []} for v in range(1, 1661)}
    totals = collections.Counter()
    milestones = []
    with compressed(out / "inventory.jsonl.gz") as inventory, compressed(out / "summaries.jsonl.gz") as summaries, compressed(out / "case-records.jsonl.gz") as cases, compressed(out / "document-events.jsonl.gz") as events:
        for folder in ROOTS:
            base = root / folder
            if not base.exists():
                continue
            for parent, dirs, files in os.walk(base, followlinks=False):
                dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS and not (Path(parent) / d).is_symlink())
                for name in sorted(files):
                    path = Path(parent) / name
                    if path.is_symlink() or not path.is_file():
                        totals["symlinks_or_nonfiles_excluded"] += 1
                        continue
                    rel = path.relative_to(root).as_posix()
                    aid = digest(rel.encode())
                    vs = versions(rel)
                    before = path.stat()
                    row = {"artifact_id": aid, "source_root": folder,
                           "version_mentions": vs, "bytes": before.st_size,
                           "suffix": path.suffix if path.suffix in {".json", ".jsonl", ".md", ".png", ".log", ".py", ".js", ".txt", ".sql", ".csv", ".html", ".zip"} else "other"}
                    try:
                        row["source_sha256"] = stream_hash(path)
                        row["disposition"] = "hash_only_private_content"
                        selected = any(s in name.lower() for s in ("summary", "provenance", "decision", "manifest"))
                        if path.suffix == ".json" and selected and before.st_size <= 16 * 1024 * 1024:
                            try:
                                data = json.loads(path.read_text())
                                safe = project(data)
                                if safe:
                                    item = {"artifact_id": aid, "source_sha256": row["source_sha256"], "version_mentions": vs, "projection": safe}
                                    emit(summaries, item)
                                    row["disposition"] = "structured_summary_projection"
                                    totals["summaries_exported"] += 1
                                    for v in vs:
                                        records[v]["summary_ids"].append(aid)
                                    if safe.get("question_count") == 2000 and "quality_metrics" in safe:
                                        milestones.append(item)
                            except (ValueError, UnicodeError):
                                row["disposition"] = "parse_error_hash_only"
                        elif path.suffix == ".jsonl" and any(s in name.lower() for s in ("result", "judgment", "failure", "verdict")):
                            exported, invalid = 0, 0
                            try:
                                with path.open() as source:
                                    for line_number, line in enumerate(source, 1):
                                        if not line.strip():
                                            continue
                                        try:
                                            data = json.loads(line)
                                        except ValueError:
                                            invalid += 1
                                            continue
                                        safe = project(data)
                                        if not safe:
                                            continue
                                        identifier = next((data[k] for k in ("case_id", "question_id", "qid", "id") if k in data), line_number)
                                        identity = json.dumps([data.get("region"), identifier], sort_keys=True)
                                        emit(cases, {"artifact_id": aid, "line": line_number,
                                                     "case_key": digest(identity.encode()), "projection": safe})
                                        exported += 1
                            except UnicodeError:
                                invalid += 1
                            row.update(disposition="case_projection", exported_rows=exported, invalid_rows=invalid)
                            totals["case_rows_exported"] += exported
                            totals["case_invalid_rows"] += invalid
                        elif path.suffix == ".md" and before.st_size <= 4 * 1024 * 1024:
                            try:
                                lines = path.read_text().splitlines()
                                heading_versions, date = [], None
                                for number, line in enumerate(lines, 1):
                                    if line.startswith("#"):
                                        heading_versions = versions(line)
                                        found = re.search(r"20\d{2}-\d{2}-\d{2}", line)
                                        date = found.group() if found else None
                                    mentioned = versions(line)
                                    if not mentioned and not heading_versions:
                                        continue
                                    ev = {"artifact_id": aid, "line": number, "line_sha256": digest(line.encode()),
                                          "version_mentions": sorted(set(mentioned + heading_versions)),
                                          "heading_versions": heading_versions, "date_in_heading": date,
                                          "is_heading": line.startswith("#"),
                                          "reported_ratios": re.findall(r"(?<![\w/])\d{1,5}/\d{1,5}(?![\w/])", line),
                                          "reported_percentages": re.findall(r"(?<![\w.])\d{1,3}(?:\.\d+)?%", line),
                                          "decision_tokens": [x for x in ("NO_GO", "NO-GO", "HOLD_UNPROVEN", "PROMOTE_CANDIDATE", "FAIL", "PASS") if re.search(r"\b" + re.escape(x) + r"\b", line)]}
                                    eid = digest((aid + ":" + str(number)).encode())
                                    ev["event_id"] = eid
                                    emit(events, ev)
                                    for v in ev["version_mentions"]:
                                        records[v]["document_events"].append(eid)
                                    totals["document_events_exported"] += 1
                                row["disposition"] = "document_event_projection"
                            except UnicodeError:
                                row["disposition"] = "parse_error_hash_only"
                        after = path.stat()
                        if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
                            row["changed_during_export"] = True
                            totals["changed_during_export"] += 1
                    except OSError as exc:
                        row["disposition"] = "read_error"
                        row["error_type"] = type(exc).__name__
                        totals["read_errors"] += 1
                    emit(inventory, row)
                    for v in vs:
                        records[v]["artifact_ids"].append(aid)
                    totals["files_inventoried"] += 1
                    totals["bytes_hashed"] += before.st_size
                    if totals["files_inventoried"] % 10000 == 0:
                        print(json.dumps(dict(totals)), flush=True)
    # Git subjects and prose are private; publish immutable references and mentions.
    commits = []
    for line in git(root, "log", "--all", "--format=%H%x09%aI%x09%s").splitlines():
        sha, date, subject = line.split("\t", 2)
        vs = versions(subject)
        commits.append({"commit": sha, "date": date, "version_mentions": vs, "subject_sha256": digest(subject.encode())})
        for v in vs:
            records[v]["commit_ids"].append(sha)
    dump(out / "git-history.json", commits)
    totals["reachable_commits_indexed"] = len(commits)
    for v, item in records.items():
        item["coverage"] = "located_references" if any(item[k] for k in ("artifact_ids", "document_events", "commit_ids")) else "not_located"
        item["attribution"] = "Mentions only; a referenced version may be a comparator, schema, or oracle version."
        dump(out / "iterations" / f"v{v:04d}.json", item)
    totals["versions_with_references"] = sum(r["coverage"] == "located_references" for r in records.values())
    totals["versions_without_references"] = 1660 - totals["versions_with_references"]
    dump(out / "full-cohort-summary-candidates.json", milestones)
    report = {"schema_version": "public_evidence_inventory.v1", "source_git_head": git(root, "rev-parse", "HEAD").strip(),
              "source_tracked_worktree_clean": not bool(git(root, "status", "--porcelain", "--untracked-files=no").strip()),
              "scope_roots": ROOTS, "version_range": [1, 1660], "counts": dict(totals),
              "limits": ["Working-tree files plus reachable Git commit metadata, not every historical Git blob.",
                         "Version mentions are not proof of separate experiments or improvements.",
                         "Only allowlisted aggregate fields and case verdicts are copied; all other content is withheld.",
                         "Hash-only artifacts cannot be independently content-reviewed without private source access.",
                         "No inferred scores, chronology, acceptance decisions, or common cohort across versions."]}
    dump(out / "coverage.json", report)
    chunks = []
    for start in range(1, 1661, 100):
        end = min(start + 99, 1660)
        name = f"v{start:04d}-v{end:04d}.md"
        lines = [f"# Version Reference Index: v{start} to v{end}", "", "Counts denote references, not successful experiments. Read the linked JSON against the archive indexes.", "", "| Version | Path artifacts | Summaries | Document events | Commits | Coverage |", "|---|---:|---:|---:|---:|---|"]
        for v in range(start, end + 1):
            r = records[v]
            lines.append(f"| [v{v}](../iterations/v{v:04d}.json) | {len(r['artifact_ids'])} | {len(r['summary_ids'])} | {len(r['document_events'])} | {len(r['commit_ids'])} | {r['coverage']} |")
        p = out / "history" / name
        p.parent.mkdir(exist_ok=True)
        p.write_text("\n".join(lines) + "\n")
        chunks.append(f"- [v{start} to v{end}](history/{name})")
    history = """# Iteration History and Evidence Coverage

This is an exhaustive index of version identifiers v1 through v1660 within the
declared local evidence scope. It is not a claim of 1,660 complete experiments,
1,660 successful improvements, or a single unchanged evaluation cohort.

## Coverage

""" + f"Files inventoried: {totals['files_inventoried']:,}. Structured summaries: {totals['summaries_exported']:,}.\nPublic case records: {totals['case_rows_exported']:,}. Versions with located references: {totals['versions_with_references']}/1660.\nVersions without located references: {totals['versions_without_references']}.\n\n" + "\n".join(chunks) + """

## Reading the Evidence

Each version links to source artifact IDs, summary IDs, document event IDs, and
Git commit hashes. Path and prose mentions may refer to an older comparator or
an oracle/schema version; they do not establish tested code identity. The
document events retain line numbers, line hashes, dates, and reported numeric
tokens. Those tokens are unverified statements until linked to a result.

`inventory.jsonl.gz` contains an entry for every regular file found in the
declared roots. `summaries.jsonl.gz`, `case-records.jsonl.gz`, and
`document-events.jsonl.gz` contain conservative public projections. Source paths
are represented by SHA-256 IDs to avoid disclosing internal names. Recompute an
ID from the UTF-8 repository-relative POSIX path using SHA-256. Original file
hashes bind projections to the private source. Public file hashes are listed in
`public-manifest.json` after verification.

## Verified Anchors

- [MVP UAT](baseline-UAT-20260608/README.md): 2,000 aggregated runs; combined
  evaluation resolves two initial Judge errors. 1,204 correct, 587 partial,
  172 incorrect, 37 refusal. Usefulness is 1,791/2,000 = 89.55%.
- [v1660](v1660-final-baseline/README.md): natural-user 2,000-case cohort,
  semantic correctness 1,451/2,000 = 72.55%, including 396 correct refusals;
  strict E2E 1,422/2,000 = 71.10%. The 85% semantic target is not reached.
- v1441: the v1660 promotion decision identifies 1,435/2,000 as its comparator.
  The accepted change is +16 cases (+0.80 percentage points). This does not
  imply every case improved or statistical significance.
- Other full-cohort summaries, including rejected candidates and intermediate
  aggregation states, are indexed in `full-cohort-summary-candidates.json`.
  They require matching question, oracle, source, model and evaluator contracts
  before comparison. A higher earlier score is not automatically a better
  candidate under a changed evaluation contract.

## Corrections to the Draft History

The earlier draft's v100/55%, v500/65%, v1000/70% milestones had no cited
evidence and are withdrawn. The 411 planner/partial cases are an owning-layer
failure bucket, not a separately validated usefulness label. The claimed 93.1%
usefulness, zero refusal, and 138 total failures are withdrawn. Local dev
acceptance as an iteration baseline is not production acceptance. No June to
September causal quality-gate improvement is inferred from unequal protocols.

## Scope and Reproduction

See [coverage.json](coverage.json), [export policy](validation-protocols/export-policy.md),
and [evaluation protocol](validation-protocols/semantic-judge-protocol.md).
Use `python tools/export_evidence.py --source /path/to/private/repository`
to rebuild from the private evidence tree. Missing or withheld artifacts remain
explicit limitations. This public release reproduces aggregate calculations,
not the proprietary corpus, runtime deployment, or independent semantic grading.
"""
    (out / "ITERATION_HISTORY.md").write_text(history)
    print(json.dumps(report, indent=2), flush=True)


if __name__ == "__main__":
    main()
