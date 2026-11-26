"""Combine the structured and documentary scans into the final navigation."""
from collections import Counter, defaultdict
import json
from pathlib import Path
import sys
import gzip

from build_review_evidence import rows, version_dir, link
from export_evidence import compressed, dump, emit


def finish(out):
    folder = out / "version-recovery"
    refs = Counter()
    for row in rows(folder / "additional-document-mentions.jsonl.gz"):
        refs.update(row["version_mentions"])
    records = json.loads((folder / "versions.json").read_text())
    embedded = defaultdict(list)
    for entry in rows(folder / "embedded-sources.jsonl.gz"):
        for version in entry["versions"]:
            embedded[version].append(entry)
    bands = defaultdict(list)
    for record in records:
        version = record["version"]
        record["additional_document_mentions"] = refs[version]
        page = version_dir(out, version) / "README.md"
        if refs[version] and record["status"] == "no_located_reference":
            record["status"] = "archive_references_only"
        before = page.read_text().split("\n## Additional recovered evidence\n")[0].rstrip()
        details = folder / record["details"]
        with gzip.open(details, "rt") as stream:
            entries = json.load(stream)
        entries = [e for e in entries if "input_format" not in e] + embedded[version]
        with compressed(details) as stream:
            emit(stream, entries)
        counts = Counter(e["status"] for e in entries)
        record["dispositions"] = dict(counts)
        record["additional_measurement_projections"] = counts["measurements"] + counts["partial_parse"]
        if record["additional_measurement_projections"]:
            record["status"] = "measured"
        elif entries and record["status"] == "no_located_reference":
            record["status"] = "archive_references_only"
        view = [before, "", "## Additional recovered evidence", "",
                f"Status: `{record['status']}`. Additional numerical projections: {record['additional_measurement_projections']}. "
                f"Additional historical document mentions: {refs[version]}.", "",
                f"[All source dispositions and measurement paths]({link(page.parent,details)}) | "
                f"[Coverage and interpretation]({link(page.parent,folder/'README.md')})."]
        available = [e for e in entries if "file" in e]
        if available:
            view.extend(["", "Selected downloads, ordered by source fingerprint. The full index above includes all available and unresolved sources.", ""])
            view.extend(f"- [{e['artifact_id'][:12]} / {e['source_sha256'][:12]}]({link(page.parent,folder/e['file'])}): `{e['origin']}`, `{e['status']}`."
                        for e in available[:12])
        page.write_text("\n".join(view) + "\n")
        bands[page.parent.parent.name].append(record)
    dump(folder / "versions.json", records)
    statuses = Counter(row["status"] for row in records)
    text = ["# Version evidence recovery", "",
            "This release audits v1 through v1660. The unit below is a version identifier. A measured version has at least one path-associated summary, case record, or numerical projection. Probes, incomplete runs, retries, and comparator mentions can all produce evidence. Completion and deployment require separate run-level evidence.", "",
            "| Status | Versions |", "|---|---:|"]
    for key in ["measured", "archive_references_only", "no_located_reference"]:
        text.append(f"| {key} | {statuses[key]} |")
    text.extend(["", "## Download and recount", "",
                 "The [version index](versions.json) has one row per identifier. Each row links to a compressed JSON list of source dispositions. Within that list, each measurement file path is relative to this directory. Artifact IDs identify source paths by hash. Source SHA-256 identifies exact bytes. Historical variants have their own fingerprints. Sources with identical bytes share a measurement download.", "",
                 "The [case-stream catalog](case-streams.jsonl.gz) indexes every original case stream by artifact ID. It reports observed rows, distinct case keys, label counts, and the number of rows with an end-to-end verdict. To retrieve the projected records for a catalog entry, filter the [original archive](../case-records.jsonl.gz) by artifact_id. Multiple streams can describe the same questions, retries or intermediate judgments. Do not add their counts as distinct cases.", "",
                 "The [full-cohort inventory](../FULL_COHORT_EVALUATIONS.md) identifies five v5 manuscript runs and links to 2,000 pseudonymous verdicts per run. The conventional control and v1660 have separate case releases under the same inventory. The [historical document index](additional-document-mentions.jsonl.gz) provides source and line fingerprints with version mentions. It contains no document text.", "",
                 "The structured scan covers JSON, JSONL, CSV, TSV and exit status files with explicit version associations within the original five private evidence roots, reachable Git revisions of those paths, and the separate versioned backups. The aligned conventional control has its own [release](../baseline-system-evaluation/README.md). The previously retired control is excluded. Earlier allowlisted results and the original inventory are preserved. Sources outside that scope (including private enterprise documents and unstructured logs or images) are not released as outcome data.", "",
                 "The [embedded source index](embedded-sources.jsonl.gz) also covers structured members of located version-associated ZIP and tar archives and JSON-formatted lines in text or log files. Only allowlisted measurements are released. Missing, malformed or unprojectable structured sources have explicit dispositions. For a partially parseable JSONL file, valid measurements retain their original line numbers, and the disposition records the invalid-line count. Where only a fingerprint or document/commit mention survives, run completion and its outcome are unknown. Missing rows carry no assumed label or score.", "",
                 "## Browse by version", ""])
    for name, group in bands.items():
        page = folder / (name + ".md")
        lines = ["# " + name, "", "[All ranges](README.md)", "",
                 "| Version | Evidence status | Existing measured sources | Additional numerical projections | New document mentions | Source dispositions |",
                 "|---|---|---:|---:|---:|---|"]
        for row in group:
            v = row["version"]
            path = version_dir(out, v) / "README.md"
            lines.append(f"| [v{v}]({link(folder,path)}) | {row['status']} | {row['existing_measured_artifacts']} | {row['additional_measurement_projections']} | {row['additional_document_mentions']} | [Download]({row['details']}) |")
        page.write_text("\n".join(lines)+"\n")
        text.append(f"- [{name}]({page.name})")
    (folder / "README.md").write_text("\n".join(text) + "\n")
    print(dict(statuses))


if __name__ == "__main__":
    finish(Path(sys.argv[1]) if len(sys.argv)>1 else Path("evidence"))
