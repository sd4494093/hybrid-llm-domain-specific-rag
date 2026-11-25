#!/usr/bin/env python3
"""Supplement the immutable inventory and publish bounded, readable review pages."""

import argparse
import collections
import gzip
import itertools
import json
import math
import os
from pathlib import Path

from export_evidence import (BOOLS, CONTAINERS, COUNTS, DIMENSIONS, ENUMS,
                             HASH_FIELDS, LABELS, MODELS, ROOTS, SKIP_DIRS,
                             digest, dump, stream_hash)


NUMBERS = COUNTS | DIMENSIONS | set("""
case_count candidate_limit semantic_weight vector_share max_documents max_segments
partition_input_count partition_input_unique_parents expected_unique_parent_first_rank
expected_parent_rrf_rank expected_parent_lane_count expected_parent_vector_rank
expected_parent_full_text_rank candidate_count candidate_unique_parents tail_count
post_rerank_count post_expansion_count rank vector_rank full_text_rank score full_text_score
semantic_vector_rank semantic_full_text_rank original_vector_rank original_full_text_rank
original_window_gain original_window_terms original_single_terms original_rerank_rank
semantic_rerank_rank semantic_rerank_score fused_rerank_rank selected_segment_count
selected_parent_count position order selected_order segment_count term_coverage
raw_max_coverage raw_total_coverage distinctive_coverage pre_rerank_score max_coverage
answer_shape_subject_coverage baseline_first_rank title_focus selection_score
translation_family_semantic_rerank_rank rank_score temporal_match_count
raw_distinctive_coverage rerank_parent_rank translation_family_fused_rerank_rank
title_coverage deep_first_rank answer_shape_score temporal_conflict_count max_score
total_coverage authority summary_hits summary_first_rank answer_shape_identifier_coverage
symbolic_definition_symbol_coverage sample_order rerank_rank document_family_semantic_rerank_rank
document_family_fused_rerank_rank fact_backstop_match_coverage fact_backstop_numeric_count
answer_shape_numeric_condition_pairs fact_candidate_order fact_candidate_family_support_count
semantic_rank instruction_score information_score reservation pass_rate
candidate_surface_exported_count candidate_document_count eligible_document_count
http_code chat_attempts retriever_resource_count answer_chars comparison_subject_count
selected_parent_competitor_score answer_shape_segment_count answer_shape_position_count
same_source_sibling_dataset_count context_segment_rerank_candidate_count
duplicate_context_segment_count unique_context_refill_count context_segment_rerank_skipped_scored_count
shard_count shard_index retry_backoff_seconds chat_retries initial_runtime_error_count
retried_runtime_error_count timeout_seconds vector_weight keyword_weight transport_ok_count
transport_failure_count transport_ok_rate retriever_snippet_chars query_count
full_cohort_question_count resumed_case_count exit_code actual_loops actual_rows plan_rows
anchor_position first_attempt_success_rate runtime_source_evidence_case_count
runtime_source_evidence_entry_count resumed_count evaluated_count retried_case_count
""".split())
FLAGS = BOOLS | set("""
proposal_partition_loaded expected_in_partition_input expected_in_candidates expected_in_tail
query_changed title_present document_name_present source_header_present
semantic_rerank_score_present expected_selected effective_document_is_self
temporal_specific_match scope_phrase_match compact_product_variant_subject archived_source
fact_backstop duplicates_selected_fact_family candidate_surface_complete
strong_title_parent_budget_eligible comparison_numeric_range_query explicit_comparison
resolved_comparison retried_runtime_error market_scope_query product_configuration_query
symbolic_definition_query normative_authority_primary status_query coherent_normative_title_source
coherent_descriptor_source initial_response_window_query numeric_specification_answer_query
numeric_constraint_answer_query same_source_answer_shape_source_protected context_segment_rerank_applied
context_rank_one_witness_protected contrast_complement_query initial_runtime_error
oracle_blind_runtime exact_cardinality expected_in_candidate_pool expected_in_eligible
expected_effective_in_eligible metadata_filter_mode_is_oracle comparison_decision_query
git_worktree_clean question_text_stored semantic_query_text_stored document_title_text_stored
source_text_stored vector_values_stored secret_values_printed vector_values_printed
full_answer_printed source_snippets_printed
""".split())
NODES = CONTAINERS | DIMENSIONS | set("""
selector_contract candidate_numeric_surface expected_partition_input expected_candidates
expected_tail selector_results semantic original expected_rows selected_segment_positions
selection_debug rerank_query_results expected_post_rerank expected_post_expansion
expected_selector_rows rows cases records judgments semantic_judgments candidates
candidate_surface selected_documents selected_segments runtime_contract shards evaluation
baseline candidate retrieval runtime selector probes expected actual
""".split())
SAFE_ENUMS = ENUMS | {"query_representation_mode"}
SAFE_LABELS = LABELS | {"runtime", "semantic", "original"}
PAGE_BYTES = 192 * 1024
PAGE_ROWS = 50


def scalar(key, value):
    if key in NUMBERS and (value is None or type(value) in (int, float) and math.isfinite(value)):
        return True, value
    if key in FLAGS and type(value) is bool:
        return True, value
    if key in SAFE_ENUMS and isinstance(value, str) and value in SAFE_LABELS:
        return True, value
    if key in {"model", "semantic_judge_model"} and isinstance(value, str) and value in MODELS:
        return True, value
    if key in HASH_FIELDS and isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdef" for c in value):
        return True, value
    return False, None


def numeric_project(value):
    """Preserve positional arrays, false and null; exclude identities and free text."""
    if isinstance(value, list):
        return [numeric_project(v) if isinstance(v, (dict, list)) else None for v in value]
    if not isinstance(value, dict):
        return {}
    out = {}
    for key, val in value.items():
        if key in NODES and isinstance(val, (dict, list)):
            out[key] = numeric_project(val)
        else:
            keep, safe = scalar(key, val)
            if keep:
                out[key] = safe
    return out


def has_measurement(value):
    if isinstance(value, dict):
        return any(has_measurement(v) for v in value.values())
    if isinstance(value, list):
        return any(has_measurement(v) for v in value)
    return value is not None


def stream_project(stream):
    """Use a streaming JSON parser so large private answers never enter the result tree."""
    import ijson
    def parse_events():
        try:
            yield from ijson.basic_parse(stream, use_float=True)
        except ijson.JSONError as exc:
            raise ValueError("Invalid JSON source") from exc

    events = iter(parse_events())

    def skip(first):
        depth = int(first[0] in {"start_map", "start_array"})
        while depth:
            event, _ = next(events)
            depth += (event in {"start_map", "start_array"}) - (event in {"end_map", "end_array"})

    def read(first):
        event, value = first
        if event == "start_array":
            result = []
            for child in events:
                if child[0] == "end_array":
                    return result
                result.append(read(child) if child[0] in {"start_map", "start_array"} else None)
        elif event == "start_map":
            result = {}
            for event, key in events:
                if event == "end_map":
                    return result
                if event != "map_key":
                    raise ValueError("Invalid map event")
                child = next(events)
                if key in NODES and child[0] in {"start_map", "start_array"}:
                    if key in result:
                        raise ValueError("Duplicate projected key")
                    result[key] = read(child)
                elif child[0] in {"start_map", "start_array"}:
                    skip(child)
                else:
                    keep, safe = scalar(key, child[1])
                    if keep:
                        if key in result:
                            raise ValueError("Duplicate projected key")
                        result[key] = safe
            raise ValueError("Incomplete JSON")
        else:
            return {}

    result = read(next(events))
    if next(events, None) is not None:
        raise ValueError("Trailing JSON")
    return result


def rows(path):
    with gzip.open(path, "rt") as stream:
        yield from map(json.loads, stream)


def encoded(value):
    return (json.dumps(value, ensure_ascii=True, sort_keys=True, indent=2) + "\n").encode()


def write_pages(folder, data):
    """Externalize large arrays losslessly; links are relative to the artifact folder."""
    paths = []

    def write(value):
        index = len(paths)
        rel = f"pages/{index // 100:04d}/{index:06d}.json"
        paths.append(rel)
        payload = encoded(value)
        if len(payload) > PAGE_BYTES:
            raise ValueError("Review page exceeds byte bound")
        path = folder / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
        return rel

    def visit(value):
        if isinstance(value, dict):
            return {k: visit(v) for k, v in value.items()}
        if not isinstance(value, list):
            return value
        items = [visit(v) for v in value]
        if len(items) <= PAGE_ROWS and len(encoded(items)) < PAGE_BYTES // 2:
            return items
        links, batch = [], []
        size = 2
        for item in items:
            item_size = len(encoded(item)) + 1
            if batch and (len(batch) >= PAGE_ROWS or size + item_size > PAGE_BYTES // 2):
                links.append(write(batch))
                batch, size = [], 2
            batch.append(item)
            size += item_size
        if batch:
            links.append(write(batch))
        return {"review_pages": links, "item_count": len(items)}

    entry = visit(data)
    folder.mkdir(parents=True, exist_ok=True)
    payload = encoded(entry)
    if len(payload) > PAGE_BYTES:
        raise ValueError("Review overview exceeds byte bound")
    (folder / "data.json").write_bytes(payload)
    # A page listing is itself split so GitHub renders every link.
    links = []
    for start in range(0, len(paths), 100):
        name = f"page-index-{start // 100:04d}.md"
        (folder / name).write_text("# Data Pages\n\nAll paths inside JSON are relative to this artifact directory.\n\n" +
                                  "\n".join(f"- [{p}]({p})" for p in paths[start:start + 100]) + "\n")
        links.append(name)
    return links, len(paths)


def artifact_dir(out, aid):
    return out / "review" / "artifacts" / aid[:2] / aid


def probe_table(value):
    if not isinstance(value, dict) or not isinstance(value.get("results"), list):
        return []
    results = value["results"]
    if not any(isinstance(r, dict) and "expected_in_candidates" in r for r in results):
        return []
    text = ["", "## Candidate Probe", "",
            f"Reported case count: {value.get('case_count', 'unreported')}; candidate limit: {value.get('candidate_limit', 'unreported')}.", "",
            "Array positions identify cases within this source only. The table shows at most ten rows; all projected data remain linked above.", "",
            "| Case position | Expected vector rank | Expected full-text rank | In input | In candidates | In tail |", "|---|---:|---:|---|---|---|"]
    keys = ("expected_parent_vector_rank", "expected_parent_full_text_rank", "expected_in_partition_input", "expected_in_candidates", "expected_in_tail")
    for index, row in enumerate(results[:10]):
        if isinstance(row, dict):
            cells = [json.dumps(row[k]) if k in row else "unreported" for k in keys]
            text.append(f"| {index + 1} | " + " | ".join(cells) + " |")
    return text


def version_dir(out, version):
    start = (version - 1) // 50 * 50 + 1
    return out / "review" / f"v{start:04d}-v{min(start + 49, 1660):04d}" / f"v{version:04d}"


def link(base, target):
    return os.path.relpath(target, base).replace(os.sep, "/")


def source_paths(root, wanted):
    found = {}
    for prefix in ROOTS:
        for parent, dirs, files in os.walk(root / prefix, followlinks=False):
            dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS and not (Path(parent) / d).is_symlink())
            for name in sorted(files):
                path = Path(parent) / name
                if path.is_symlink():
                    continue
                aid = digest(path.relative_to(root).as_posix().encode())
                if aid in wanted:
                    found[aid] = path
    return found


def supplement(path, original):
    if path is None:
        return "source_missing", None
    before = path.stat()
    if before.st_size != original["bytes"] or stream_hash(path) != original["source_sha256"]:
        return "source_changed_since_inventory", None
    try:
        if path.suffix == ".json":
            with path.open("rb") as stream:
                value = stream_project(stream)
        else:
            value = []
            with path.open() as stream:
                for line, raw in enumerate(stream, 1):
                    if raw.strip():
                        safe = numeric_project(json.loads(raw))
                        value.append({"line": line, "measurements": safe})
            if not any(has_measurement(row["measurements"]) for row in value):
                value = {}
    except (ValueError, UnicodeError, StopIteration, OverflowError):
        return "parse_error", None
    after = path.stat()
    if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        return "source_changed_during_read", None
    return ("numeric_content", value) if has_measurement(value) else ("no_allowlisted_measurements", None)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("evidence"))
    args = parser.parse_args()
    out, root = args.output.resolve(), args.source.resolve()
    if out.is_relative_to(root):
        parser.error("Output must be outside the private source repository")
    if (out / "review").exists():
        parser.error("Archive the previous review directory before rebuilding; files are never deleted")
    inventory = {r["artifact_id"]: r for r in rows(out / "inventory.jsonl.gz")}
    versions = {v: json.loads((out / "iterations" / f"v{v:04d}.json").read_text()) for v in range(1, 1661)}
    wanted = set().union(*(set(v["artifact_ids"]) for v in versions.values()))
    candidates = {aid for aid in wanted if any(v >= 1000 for v in inventory[aid]["version_mentions"])
                  and (inventory[aid]["suffix"] == ".json" or
                       inventory[aid]["suffix"] == ".jsonl" and inventory[aid]["disposition"] != "case_projection")}
    paths = source_paths(root, candidates)
    summaries = {r["artifact_id"]: r for r in rows(out / "summaries.jsonl.gz") if r["artifact_id"] in wanted}
    events = collections.defaultdict(list)
    version_events = collections.defaultdict(list)
    for row in rows(out / "document-events.jsonl.gz"):
        if row["artifact_id"] in wanted:
            events[row["artifact_id"]].append(row)
        for v in row["version_mentions"]:
            version_events[v].append(row)
    commits = {r["commit"]: r for r in json.loads((out / "git-history.json").read_text())}
    status = {}
    totals = collections.Counter()

    def publish(aid, cases=None):
        original = inventory[aid]
        binding = {k: original[k] for k in ("artifact_id", "source_sha256")}
        data = {"source": binding, "original_inventory": original}
        kinds = []
        if aid in summaries:
            data["archived_summary"] = summaries[aid]
            kinds.append("summary")
        if cases:
            data["case_records"] = cases
            kinds.append("case_records")
            totals["case_records"] += len(cases)
        if aid in events:
            data["document_events"] = events[aid]
            kinds.append("document_events")
        disposition = "not_selected_for_supplement"
        if aid in candidates:
            try:
                disposition, value = supplement(paths.get(aid), original)
            except OSError:
                disposition, value = "source_read_error", None
            if value is not None:
                data["measurements"] = value
                kinds.append("numeric_content")
            totals["supplement_" + disposition] += 1
        data["supplement_disposition"] = disposition
        folder = artifact_dir(out, aid)
        links, pages = write_pages(folder, data)
        text = ["# Source Artifact " + aid[:12], "", f"Original type: `{original['suffix']}`. Source SHA-256: `{original['source_sha256']}`.", "",
                f"Public content: {', '.join(kinds) or 'fingerprint only; no reviewable test result'}. Supplement: `{disposition}`.", "",
                "[Read data](data.json)", "", "Data page references inside JSON are relative to this artifact directory.", "",
                "Source paths, identities, questions, answers and rationales are withheld. Array positions are retained; empty objects or null placeholders mean omitted content, not successful cases.", ""]
        text.extend(f"- [Data pages {i + 1}]({p})" for i, p in enumerate(links))
        text.extend(probe_table(data.get("measurements")))
        (folder / "README.md").write_text("\n".join(text).rstrip() + "\n")
        status[aid] = {"content": kinds, "supplement": disposition, "case_rows": len(cases or []), "data_pages": pages}
        totals["artifacts"] += 1
        totals["artifacts_with_test_content"] += bool(set(kinds) & {"summary", "case_records", "numeric_content"})
        if totals["artifacts"] % 1000 == 0:
            print(json.dumps(dict(totals)), flush=True)

    # Original JSONL export groups contiguous rows by source file.
    for aid, group in itertools.groupby(rows(out / "case-records.jsonl.gz"), key=lambda r: r["artifact_id"]):
        if aid in wanted:
            if aid in status:
                raise ValueError("Non-contiguous source records")
            publish(aid, list(group))
    for aid in sorted(wanted - status.keys()):
        publish(aid)

    ranges = []
    for start in range(1, 1661, 50):
        end = min(start + 49, 1660)
        band = version_dir(out, start).parent
        band.mkdir(parents=True, exist_ok=True)
        lines = [f"# v{start} to v{end}", "", "[All version ranges](../README.md)", "",
                 "Counts describe path-associated files, not independent experiments.", "",
                 "| Version | Test-content artifacts | Fingerprint/event-only artifacts | Cases |", "|---|---:|---:|---:|"]
        for v in range(start, end + 1):
            record = versions[v]
            folder = version_dir(out, v)
            folder.mkdir(parents=True, exist_ok=True)
            aids = record["artifact_ids"]
            substantive = sum(bool(set(status[aid]["content"]) & {"summary", "case_records", "numeric_content"}) for aid in aids)
            case_rows = sum(status[aid]["case_rows"] for aid in aids)
            totals["versions_with_test_content"] += bool(substantive)
            if v >= 1000:
                totals["v1000_plus_versions_with_test_content"] += bool(substantive)
            references = {"version": f"v{v}", "artifacts": [{"artifact_id": aid, **status[aid]} for aid in aids],
                          "document_events": version_events[v], "commits": [commits[c] for c in record["commit_ids"]]}
            write_pages(folder, references)
            entries = []
            for offset in range(0, len(aids), 50):
                name = f"artifacts-{offset // 50 + 1:03d}.md"
                rows_md = [f"# v{v}: Artifacts {offset + 1} to {min(offset + 50, len(aids))}", "", "[Version overview](README.md)", "",
                           "JSON probe cases are inside the linked numerical data; the last column counts archived JSONL records only.", "",
                           "| Source artifact | Public content | Supplement disposition | Archived JSONL rows |", "|---|---|---|---:|"]
                for aid in aids[offset:offset + 50]:
                    s = status[aid]
                    rows_md.append(f"| [{aid[:12]}]({link(folder, artifact_dir(out, aid) / 'README.md')}) | {', '.join(s['content']) or 'fingerprint only'} | {s['supplement']} | {s['case_rows']} |")
                (folder / name).write_text("\n".join(rows_md) + "\n")
                entries.append(f"- [Artifacts {offset + 1}-{min(offset + 50, len(aids))}]({name})")
            readme = [f"# v{v}: Reviewable Evidence", "", "[Version range](../README.md) | [Reference data, events and commits](data.json)", "",
                      f"{len(aids)} path-associated files: **{substantive} with test content**, {len(aids) - substantive} fingerprint/event-only. "
                      f"{case_rows} archived case records (retries and overlapping runs are not deduplicated).", "",
                      f"Document references: {len(record['document_events'])}; commit references: {len(record['commit_ids'])}.", "",
                      "A version mention may be a comparator or schema revision, not the executing version. Small probes are not full-cohort accuracy measurements.", "",
                      "The linked artifacts contain actual allowlisted measurements or per-case verdicts where available. Fingerprint-only entries do not establish test outcomes.", ""]
            if not aids:
                readme.append("No path-associated artifact was located in the archived inventory. Document/commit mentions, when present, do not fill that gap.")
            readme.extend(entries)
            readme.extend(f"- [Reference data page index]({p.name})" for p in sorted(folder.glob("page-index-*.md")))
            (folder / "README.md").write_text("\n".join(readme).rstrip() + "\n")
            old = out / "iteration-milestones" / f"v{v:04d}" / "README.md"
            banner = "## Read Actual Evidence\n\n" + f"[Open paginated results, case verdicts, and explicit gaps]({link(old.parent, folder / 'README.md')}). " + f"{substantive} path-associated artifacts have public test content.\n\n"
            original_text = old.read_text().replace(
                "No structured summary located by version-associated path. Consult document events and commit references; no score is inferred.",
                "The original summary-only export contained no summary for this version. Supplemental numerical results and case files, when available, are linked above; no score is inferred.")
            if "## Read Actual Evidence" not in original_text:
                heading, body = original_text.split("\n", 1)
                old.write_text(heading + "\n\n" + banner + body.lstrip("\n"))
            else:
                old.write_text(original_text)
            lines.append(f"| [v{v}](v{v:04d}/README.md) | {substantive} | {len(aids) - substantive} | {case_rows} |")
        (band / "README.md").write_text("\n".join(lines) + "\n")
        ranges.append(f"- [v{start}-v{end}]({band.name}/README.md)")
    dump(out / "review" / "coverage.json", {"scope": "all_version_navigation_and_archived_content; supplemental_JSON_JSONL_for_v1000_to_v1660",
         "inventory_sha256": stream_hash(out / "inventory.jsonl.gz"), "counts": dict(totals),
         "limits": ["Original snapshot retained; missing or changed private sources are not replaced.",
                    "Allowlisted measurements only, not full private artifacts or independent semantic regrading.",
                    "Version association is not execution identity; case counts include overlapping runs."]})
    dump(out / "review" / "artifact-status.json", status)
    (out / "review" / "README.md").write_text("# Paginated Evidence Review\n\n"
        "Each range contains at most 50 versions. Follow a version to its artifact tables, then open actual data and numbered pages. "
        "This avoids GitHub's truncated directory listing without removing historical links.\n\n"
        "Supplemental numerical JSON/JSONL results cover v1000-v1660; archived summaries and case verdicts are readable for all located versions. "
        "Original content is still withheld where it cannot be safely projected. A fingerprint is not a test result.\n\n"
        "[Coverage and limitations](coverage.json) | [Export policy](../validation-protocols/export-policy.md)\n\n" + "\n".join(ranges) + "\n")
    (out / "iteration-milestones" / "README.md").write_text("# Iteration Evidence\n\n"
        "GitHub truncates this legacy directory because it contains 1,660 version folders. No version is removed.\n\n"
        "**[Use the complete paginated evidence browser](../review/README.md)** to reach all versions and actual result files.\n")
    print(json.dumps(dict(totals), indent=2))


if __name__ == "__main__":
    main()
