#!/usr/bin/env python3
"""Verify the readable browser against the immutable public snapshot."""

import collections
import hashlib
import itertools
import json
from pathlib import Path

from build_review_evidence import (PAGE_BYTES, artifact_dir, encoded, numeric_project,
                                   rows, version_dir)
from export_evidence import stream_hash


def restore(folder, value, visited=None):
    visited = set() if visited is None else visited
    if isinstance(value, dict):
        if set(value) == {"review_pages", "item_count"}:
            result = []
            for rel in value["review_pages"]:
                path = (folder / rel).resolve()
                assert path.is_relative_to(folder.resolve()), "Page escapes artifact"
                assert path not in visited, "Repeated/cyclic page"
                visited.add(path)
                assert path.stat().st_size <= PAGE_BYTES, "Page too large"
                page = json.loads(path.read_text())
                assert isinstance(page, list), "Page must be an array"
                assert len(page) <= 50, "Too many page rows"
                result.extend(restore(folder, page, visited))
            assert len(result) == value["item_count"], "Page row loss"
            return result
        return {k: restore(folder, v, visited) for k, v in value.items()}
    if isinstance(value, list):
        return [restore(folder, v, visited) for v in value]
    return value


def load(folder):
    visited = set()
    result = restore(folder, json.loads((folder / "data.json").read_text()), visited)
    assert visited == {p.resolve() for p in (folder / "pages").rglob("*.json")}, "Unlinked page"
    return result


def main():
    out = Path(__file__).resolve().parents[1] / "evidence"
    review = out / "review"
    coverage = json.loads((review / "coverage.json").read_text())
    assert coverage["inventory_sha256"] == stream_hash(out / "inventory.jsonl.gz")
    status = json.loads((review / "artifact-status.json").read_text())
    inventory = {r["artifact_id"]: r for r in rows(out / "inventory.jsonl.gz")}
    summaries = {r["artifact_id"]: r for r in rows(out / "summaries.jsonl.gz")}
    events = collections.defaultdict(list)
    for row in rows(out / "document-events.jsonl.gz"):
        events[row["artifact_id"]].append(row)
    case_hashes = {}
    for aid, group in itertools.groupby(rows(out / "case-records.jsonl.gz"), lambda r: r["artifact_id"]):
        h = hashlib.sha256()
        for row in group:
            h.update(encoded(row))
        assert aid not in case_hashes
        case_hashes[aid] = h.hexdigest()
    expected = {aid for aid, row in inventory.items() if row["version_mentions"]}
    assert set(status) == expected, "Missing artifact dispositions"
    totals = collections.Counter()
    for aid, metadata in status.items():
        folder = artifact_dir(out, aid)
        data = load(folder)
        assert data["original_inventory"] == inventory[aid]
        assert data["source"] == {k: inventory[aid][k] for k in ("artifact_id", "source_sha256")}
        kinds = []
        if aid in summaries:
            assert data["archived_summary"] == summaries[aid]
            kinds.append("summary")
        if aid in case_hashes:
            h = hashlib.sha256()
            for row in data["case_records"]:
                assert row["artifact_id"] == aid
                h.update(encoded(row))
            assert h.hexdigest() == case_hashes[aid], "Case records differ from snapshot"
            assert len(data["case_records"]) == metadata["case_rows"]
            totals["case_records"] += metadata["case_rows"]
            kinds.append("case_records")
        if aid in events:
            assert data["document_events"] == events[aid]
            kinds.append("document_events")
        disposition = data["supplement_disposition"]
        assert disposition == metadata["supplement"]
        if disposition != "not_selected_for_supplement":
            totals["supplement_" + disposition] += 1
        if disposition == "numeric_content":
            value = data["measurements"]
            if inventory[aid]["suffix"] == ".jsonl":
                for row in value:
                    assert set(row) == {"line", "measurements"}
                    assert row["measurements"] == numeric_project(row["measurements"])
            else:
                assert value == numeric_project(value), "Supplement allowlist mismatch"
            kinds.append("numeric_content")
        else:
            assert "measurements" not in data
        assert kinds == metadata["content"]
        totals["artifacts"] += 1
        totals["artifacts_with_test_content"] += bool(set(kinds) & {"summary", "case_records", "numeric_content"})
    commits = {r["commit"]: r for r in json.loads((out / "git-history.json").read_text())}
    by_version = collections.defaultdict(list)
    for group in events.values():
        for row in group:
            for v in row["version_mentions"]:
                by_version[v].append(row)
    for v in range(1, 1661):
        original = json.loads((out / "iterations" / f"v{v:04d}.json").read_text())
        data = load(version_dir(out, v))
        assert data["artifacts"] == [{"artifact_id": aid, **status[aid]} for aid in original["artifact_ids"]]
        assert data["document_events"] == by_version[v]
        assert data["commits"] == [commits[c] for c in original["commit_ids"]]
        substantive = any(set(status[aid]["content"]) & {"summary", "case_records", "numeric_content"} for aid in original["artifact_ids"])
        totals["versions_with_test_content"] += substantive
        if v >= 1000:
            totals["v1000_plus_versions_with_test_content"] += substantive
    assert dict(totals) == coverage["counts"], "Browser coverage mismatch"
    for folder in review.rglob("*"):
        if folder.is_dir():
            assert len(list(folder.iterdir())) <= 1000, "GitHub directory listing would truncate"
    print(json.dumps({"review_browser": "PASS", **dict(totals)}, indent=2))


if __name__ == "__main__":
    main()
