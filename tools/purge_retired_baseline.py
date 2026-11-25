#!/usr/bin/env python3
"""Remove one retired private run's public projections by source-path identity."""

import argparse
import collections
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import tempfile

from build_review_evidence import artifact_dir, link, version_dir, write_pages
from export_evidence import compressed, dump, emit, stream_hash
from verify_review_evidence import load as load_review


VERSIONS = range(1, 1661)
CONTENT_KINDS = {"summary", "case_records", "numeric_content"}


def gz_rows(path):
    with gzip.open(path, "rt", encoding="utf-8") as stream:
        yield from map(json.loads, stream)


def filter_gzip(path, remove):
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    import os
    os.close(fd)
    temp = Path(temp_name)
    try:
        with temp.open("wb") as raw, gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0, compresslevel=6) as out:
            for row in gz_rows(path):
                if not remove(row):
                    emit(out, row)
        temp.replace(path)
    finally:
        temp.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True,
                        help="The exact superseded semantic-oracle run directory")
    parser.add_argument("--evidence", type=Path, default=Path("evidence"))
    args = parser.parse_args()
    source = args.source.resolve(strict=True)
    private_root = source.parents[2]
    evidence = args.evidence.resolve(strict=True)
    inventory_path = evidence / "inventory.jsonl.gz"
    inventory = {row["artifact_id"]: row for row in gz_rows(inventory_path)}

    source_paths = {hashlib.sha256(p.relative_to(private_root).as_posix().encode()).hexdigest()
                    for p in source.rglob("*") if p.is_file()}
    matched = source_paths
    if not source_paths:
        raise SystemExit("The selected old-run directory has no files; refusing a broad purge")

    summary_ids = {row["artifact_id"] for row in gz_rows(evidence / "summaries.jsonl.gz")
                   if row["artifact_id"] in matched}
    case_counts = collections.Counter(row["artifact_id"] for row in gz_rows(evidence / "case-records.jsonl.gz")
                                      if row["artifact_id"] in matched)
    event_ids = {row["event_id"] for row in gz_rows(evidence / "document-events.jsonl.gz")
                 if row["artifact_id"] in matched}
    retired = matched

    filter_gzip(inventory_path, lambda row: row["artifact_id"] in matched)
    filter_gzip(evidence / "summaries.jsonl.gz", lambda row: row["artifact_id"] in matched)
    filter_gzip(evidence / "case-records.jsonl.gz", lambda row: row["artifact_id"] in matched)
    filter_gzip(evidence / "document-events.jsonl.gz", lambda row: row["artifact_id"] in matched)
    for aid in summary_ids:
        (evidence / "summaries" / f"{aid}.json").unlink(missing_ok=True)
    for aid in matched:
        folder = artifact_dir(evidence, aid)
        if folder.exists():
            shutil.rmtree(folder)

    # Remove the retired source's path, summary, event, and case references from
    # every indexed iteration while retaining unrelated artifacts and commits.
    affected = set()
    for version in VERSIONS:
        path = evidence / "iterations" / f"v{version:04d}.json"
        record = json.loads(path.read_text())
        before = len(record["artifact_ids"]) + len(record["summary_ids"]) + len(record["document_events"])
        record["artifact_ids"] = [aid for aid in record["artifact_ids"] if aid not in matched]
        record["summary_ids"] = [aid for aid in record["summary_ids"] if aid not in matched]
        record["document_events"] = [eid for eid in record["document_events"] if eid not in event_ids]
        after = len(record["artifact_ids"]) + len(record["summary_ids"]) + len(record["document_events"])
        if before != after:
            affected.add(version)
            dump(path, record)

    for path in (evidence / "full-cohort-summary-candidates.json",):
        rows = json.loads(path.read_text())
        dump(path, [row for row in rows if row["artifact_id"] not in matched])

    status_path = evidence / "review" / "artifact-status.json"
    status = json.loads(status_path.read_text())
    for aid in matched:
        status.pop(aid, None)
    dump(status_path, status)

    # Rebuild only affected version pages, not the complete 1,660-version browser.
    for version in sorted(affected):
        folder = version_dir(evidence, version)
        data = load_review(folder)
        data["artifacts"] = [row for row in data["artifacts"] if row["artifact_id"] not in matched]
        data["document_events"] = [row for row in data["document_events"] if row.get("event_id") not in event_ids]
        pages_dir = folder / "pages"
        if pages_dir.exists():
            shutil.rmtree(pages_dir)
        for path in folder.glob("page-index-*.md"):
            path.unlink()
        write_pages(folder, data)

        record = json.loads((evidence / "iterations" / f"v{version:04d}.json").read_text())
        aids = record["artifact_ids"]
        lines = [
            f"# v{version}: Artifacts", "", "[Version overview](README.md)", "",
            "| Source artifact | Public content | Supplement disposition | Archived JSONL rows |",
            "|---|---|---|---:|",
        ]
        for offset in range(0, len(aids), 50):
            name = f"artifacts-{offset // 50 + 1:03d}.md"
            subset = aids[offset:offset + 50]
            rows = [
                f"| [{aid[:12]}]({link(folder, artifact_dir(evidence, aid) / 'README.md')}) | "
                f"{', '.join(status[aid]['content']) or 'fingerprint only'} | "
                f"{status[aid]['supplement']} | {status[aid]['case_rows']} |"
                for aid in subset
            ]
            (folder / name).write_text("\n".join([
                f"# v{version}: Artifacts {offset + 1} to {offset + len(subset)}", "",
                "[Version overview](README.md)", "",
                "JSON probe cases are inside linked numerical data; the last column counts archived JSONL records only.",
                "", "| Source artifact | Public content | Supplement disposition | Archived JSONL rows |",
                "|---|---|---|---:|", *rows, "",
            ]))
        summary_ids_for_version = record["summary_ids"]
        summary_map = {row["artifact_id"]: row for row in gz_rows(evidence / "summaries.jsonl.gz")}
        summary_lines = []
        for aid in summary_ids_for_version:
            row = summary_map.get(aid)
            if not row:
                continue
            projection = row["projection"]
            metric = projection.get("quality_metrics", {}).get("semantic_correctness_rate", {})
            semantic = f"{metric['numerator']}/{metric['denominator']}" if "numerator" in metric else "unreported"
            count = projection.get("question_count", projection.get("total_rows", projection.get("total", "unreported")))
            summary_lines.append((aid, f"{count} | {projection.get('status', 'unreported')} | "
                                  f"{semantic} | {projection.get('e2e_pass_count', 'unreported')} |"))

        def summary_links(base):
            return [f"| [{aid[:12]}]({link(base, evidence / 'summaries' / f'{aid}.json')}) | {cells}"
                    for aid, cells in summary_lines]
        readme = [
            f"# v{version}: Reviewable Evidence", "",
            "[Version range](../README.md) | [Reference data, events and commits](data.json)", "",
            f"{len(aids)} path-associated files: {sum(bool(set(status[aid]['content']) & CONTENT_KINDS) for aid in aids)} "
            f"with test content. {sum(status[aid]['case_rows'] for aid in aids)} archived case records.", "",
            "A version mention may be a comparator or schema revision, not the executing version.", "",
            "| Artifact | Cases or rows | Status | Semantic numerator/denominator | E2E pass |",
            "|---|---:|---|---|---|", *summary_links(folder), "",
        ]
        (folder / "README.md").write_text("\n".join(readme))

        milestone = evidence / "iteration-milestones" / f"v{version:04d}"
        if milestone.exists():
            old = json.loads((milestone / "summary.json").read_text())
            old["summary_artifact_ids"] = [aid for aid in old.get("summary_artifact_ids", []) if aid not in matched]
            dump(milestone / "summary.json", old)
            mlines = [f"# v{version}: Located Evidence", "",
                      f"Coverage: `{record['coverage']}`. This version has {len(aids)} path-associated artifacts, "
                      f"{len(record['document_events'])} document references, and {len(record['commit_ids'])} commit-subject references.",
                      "", "Path mentions can identify comparators or schema revisions, not verified execution identity.",
                      "", f"[Reference IDs](../../iterations/v{version:04d}.json) | [Full history](../../ITERATION_HISTORY.md)",
                      "", "| Artifact | Cases or rows | Status | Semantic numerator/denominator | E2E pass |",
                      "|---|---:|---|---|---|", *summary_links(milestone), ""]
            (milestone / "README.md").write_text("\n".join(mlines))

    for start in range(1, 1661, 50):
        end = min(start + 49, 1660)
        versions = range(start, end + 1)
        review_band = evidence / "review" / f"v{start:04d}-v{end:04d}" / "README.md"
        table = ["| Version | Test-content artifacts | Fingerprint/event-only artifacts | Cases |",
                 "|---|---:|---:|---:|"]
        for version in versions:
            record = json.loads((evidence / "iterations" / f"v{version:04d}.json").read_text())
            aids = record["artifact_ids"]
            content = sum(bool(set(status[aid]["content"]) & CONTENT_KINDS) for aid in aids)
            case_rows = sum(status[aid]["case_rows"] for aid in aids)
            table.append(f"| [v{version}](v{version:04d}/README.md) | {content} | {len(aids)-content} | {case_rows} |")
        header = [f"# v{start} to v{end}", "",
                  "[All version ranges](../README.md)", "",
                  "Counts describe path-associated files, not independent experiments.", ""]
        review_band.write_text("\n".join(header + table) + "\n")

    inventory_rows = list(gz_rows(inventory_path))
    summary_rows = list(gz_rows(evidence / "summaries.jsonl.gz"))
    case_total = sum(1 for _ in gz_rows(evidence / "case-records.jsonl.gz"))
    event_total = sum(1 for _ in gz_rows(evidence / "document-events.jsonl.gz"))
    coverage_path = evidence / "coverage.json"
    coverage = json.loads(coverage_path.read_text())
    commits = json.loads((evidence / "git-history.json").read_text())
    versions_with_refs = 0
    for version in VERSIONS:
        row = json.loads((evidence / "iterations" / f"v{version:04d}.json").read_text())
        versions_with_refs += bool(row["artifact_ids"] or row["summary_ids"] or row["document_events"] or row["commit_ids"])
    coverage["counts"].update({
        "files_inventoried": len(inventory_rows),
        "bytes_hashed": sum(row["bytes"] for row in inventory_rows),
        "summaries_exported": len(summary_rows),
        "case_rows_exported": case_total,
        "document_events_exported": event_total,
        "versions_with_references": versions_with_refs,
        "versions_without_references": 1660 - versions_with_refs,
    })
    dump(coverage_path, coverage)

    review_coverage_path = evidence / "review" / "coverage.json"
    review = json.loads(review_coverage_path.read_text())
    totals = collections.Counter()
    for aid, row in status.items():
        totals["artifacts"] += 1
        totals["artifacts_with_test_content"] += bool(set(row["content"]) & CONTENT_KINDS)
        totals["case_records"] += row["case_rows"]
        if row["supplement"] != "not_selected_for_supplement":
            totals["supplement_" + row["supplement"]] += 1
    for version in VERSIONS:
        record = json.loads((evidence / "iterations" / f"v{version:04d}.json").read_text())
        aids = record["artifact_ids"]
        has_content = any(set(status[aid]["content"]) & CONTENT_KINDS for aid in aids)
        totals["versions_with_test_content"] += bool(has_content)
        if version >= 1000:
            totals["v1000_plus_versions_with_test_content"] += bool(has_content)
    review["inventory_sha256"] = stream_hash(inventory_path)
    review["counts"] = dict(totals)
    dump(review_coverage_path, review)

    candidate_rows = json.loads((evidence / "full-cohort-summary-candidates.json").read_text())
    lines = ["# Full-Cohort Evaluation Inventory", "",
             "All remaining 2,000-case evaluation summaries are retained, including intermediate and rejected results.",
             "", "Match provenance and acceptance evidence before comparing rows.", "",
             "| Referenced versions | Artifact | Semantic correct / total | E2E pass | Judge errors | Judge uncertain |",
             "|---|---|---|---|---|---|"]
    for row in candidate_rows:
        projection = row["projection"]
        metric = projection["quality_metrics"]["semantic_correctness_rate"]
        versions = ", ".join("v" + str(v) for v in row["version_mentions"]) or "unattributed"
        lines.append(f"| {versions} | [{row['artifact_id'][:12]}](summaries/{row['artifact_id']}.json) | "
                     f"{metric['numerator']}/{metric['denominator']} | {projection.get('e2e_pass_count', 'unreported')} | "
                     f"{projection.get('semantic_judge_error_count', 'unreported')} | "
                     f"{projection.get('semantic_judge_uncertain_count', 'unreported')} |")
    (evidence / "FULL_COHORT_EVALUATIONS.md").write_text("\n".join(lines) + "\n")

    print(json.dumps({"retired_source_files": len(matched), "retired_summary_rows": len(summary_ids),
                      "remaining_matching_inventory": len(matched & {r["artifact_id"] for r in inventory_rows}),
                      "affected_iterations": sorted(affected)},
                     indent=2))


if __name__ == "__main__":
    main()
