#!/usr/bin/env python3
"""Validate public projections, joins, labels, links, and release fingerprints."""

import argparse
import collections
import gzip
import json
from pathlib import Path
import re
import subprocess
import sys

from export_evidence import dump, project, stream_hash


HEX = re.compile(r"^[a-f0-9]{64}$")
FORBIDDEN = re.compile(r"https?://|sharepoint\.com|/home/|Bearer\s|-----BEGIN [A-Z ]*PRIVATE KEY|\bsk-[a-zA-Z0-9]{16,}|[\w.+-]+@[\w.-]+\.[a-zA-Z]{2,}", re.I)


def fail_if(condition, message):
    if condition:
        raise ValueError(message)


def lines(path):
    with gzip.open(path, "rt") as stream:
        for number, line in enumerate(stream, 1):
            fail_if(bool(FORBIDDEN.search(line)), f"Sensitive marker: {path.name}:{number}")
            row = json.loads(line)
            if "projection" in row:
                fail_if(project(row["projection"]) != row["projection"], f"Projection schema mismatch: {path.name}:{number}")
            yield row


def check_binding(data, inventory):
    if isinstance(data, dict):
        if "source" in data and isinstance(data["source"], dict) and "artifact_id" in data["source"]:
            source = data["source"]
            fail_if(inventory[source["artifact_id"]]["source_sha256"] != source["source_sha256"], "Source fingerprint mismatch")
        if "projection" in data:
            fail_if(project(data["projection"]) != data["projection"], "Invalid curated projection")
        for value in data.values():
            check_binding(value, inventory)
    elif isinstance(data, list):
        for value in data:
            check_binding(value, inventory)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-manifest", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    out = root / "evidence"
    coverage = json.loads((out / "coverage.json").read_text())
    counts = coverage["counts"]
    fail_if(counts.get("read_errors", 0) or counts.get("changed_during_export", 0) or counts.get("case_invalid_rows", 0), "Export has unresolved read/change/parse issues")
    inventory = {}
    dispositions = collections.Counter()
    for row in lines(out / "inventory.jsonl.gz"):
        aid = row["artifact_id"]
        fail_if(aid in inventory or not HEX.fullmatch(aid), "Duplicate/invalid artifact ID")
        fail_if(not HEX.fullmatch(row.get("source_sha256", "")), "Missing source hash")
        inventory[aid] = row
        dispositions[row["disposition"]] += 1
    fail_if(len(inventory) != counts["files_inventoried"], "Inventory count mismatch")
    summaries = {}
    for row in lines(out / "summaries.jsonl.gz"):
        aid = row["artifact_id"]
        fail_if(aid in summaries or inventory[aid]["source_sha256"] != row["source_sha256"], "Summary binding mismatch")
        fail_if(json.loads((out / "summaries" / f"{aid}.json").read_text()) != row, "Readable summary drift")
        summaries[aid] = row
    fail_if(len(summaries) != counts["summaries_exported"], "Summary count mismatch")
    case_count = collections.Counter()
    for row in lines(out / "case-records.jsonl.gz"):
        fail_if(row["artifact_id"] not in inventory or not HEX.fullmatch(row["case_key"]), "Invalid case reference")
        case_count[row["artifact_id"]] += 1
    fail_if(sum(case_count.values()) != counts["case_rows_exported"], "Case count mismatch")
    for aid, amount in case_count.items():
        fail_if(inventory[aid].get("exported_rows") != amount, "Per-artifact case count mismatch")
    event_ids = set()
    for row in lines(out / "document-events.jsonl.gz"):
        fail_if(row["artifact_id"] not in inventory or row["event_id"] in event_ids, "Invalid event reference")
        event_ids.add(row["event_id"])
    fail_if(len(event_ids) != counts["document_events_exported"], "Event count mismatch")
    commits = {r["commit"] for r in json.loads((out / "git-history.json").read_text())}
    fail_if(len(commits) != counts["reachable_commits_indexed"], "Commit count mismatch")
    located = 0
    for v in range(1, 1661):
        data = json.loads((out / "iterations" / f"v{v:04d}.json").read_text())
        fail_if(data["version"] != f"v{v}", "Wrong version index")
        fail_if(not set(data["artifact_ids"]) <= inventory.keys(), "Missing artifact reference")
        fail_if(not set(data["summary_ids"]) <= summaries.keys(), "Missing summary reference")
        fail_if(not set(data["document_events"]) <= event_ids, "Missing event reference")
        fail_if(not set(data["commit_ids"]) <= commits, "Missing commit reference")
        located += data["coverage"] == "located_references"
    fail_if(located != counts["versions_with_references"], "Version coverage mismatch")
    for path in out.rglob("*"):
        if path.suffix not in {".json", ".md"} or path.name == "public-manifest.json":
            continue
        content = path.read_text()
        fail_if(bool(FORBIDDEN.search(content)), f"Sensitive marker: {path.relative_to(root)}")
        if path.suffix == ".json":
            data = json.loads(content)
            check_binding(data, inventory)
    # Validate relative Markdown links throughout the public repository.
    for path in root.rglob("*.md"):
        if ".git" in path.parts:
            continue
        for link in re.findall(r"\]\(([^)]+)\)", path.read_text()):
            if "://" in link or link.startswith("#"):
                continue
            target = (path.parent / link.split("#")[0]).resolve()
            fail_if(not target.exists(), f"Broken link: {path.relative_to(root)} -> {link}")
    subprocess.run([sys.executable, str(root / "framework/evaluation/recompute.py")], check=True)
    report = {"status": "PASS", "scope": "public_projection_integrity_not_private_content_correctness",
              "inventory_files": len(inventory), "summaries": len(summaries), "case_rows": sum(case_count.values()),
              "document_events": len(event_ids), "versions_checked": 1660, "versions_with_references": located,
              "dispositions": dict(dispositions)}
    if args.write_manifest:
        dump(out / "verification.json", report)
        manifest = {}
        for path in sorted(root.rglob("*")):
            if not path.is_file() or ".git" in path.parts or "__pycache__" in path.parts or path == out / "public-manifest.json":
                continue
            fail_if(path.stat().st_size >= 100 * 1024 * 1024, "File exceeds GitHub normal Git limit")
            manifest[path.relative_to(root).as_posix()] = {"sha256": stream_hash(path), "bytes": path.stat().st_size}
        dump(out / "public-manifest.json", manifest)
    else:
        manifest = json.loads((out / "public-manifest.json").read_text())
        current = {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file() and ".git" not in p.parts and "__pycache__" not in p.parts and p != out / "public-manifest.json"}
        fail_if(current != set(manifest), "Release file set differs from manifest")
        for rel, item in manifest.items():
            fail_if(stream_hash(root / rel) != item["sha256"], f"Public fingerprint mismatch: {rel}")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
