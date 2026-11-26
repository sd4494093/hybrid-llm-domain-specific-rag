"""Validate recovered data using only the public release."""
from collections import Counter, defaultdict
import gzip
import json
from pathlib import Path
import re

from build_review_evidence import numeric_project, rows
from recover_version_evidence import RUNS


def read_gzip(path):
    with gzip.open(path, "rt") as stream:
        return json.load(stream)


def verify(out):
    folder = out / "version-recovery"
    version_rows = json.loads((folder / "versions.json").read_text())
    assert [r["version"] for r in version_rows] == list(range(1,1661))
    files = set()
    statuses = Counter()
    for row in version_rows:
        statuses[row["status"]] += 1
        entries = read_gzip(folder / row["details"])
        counts = Counter(e["status"] for e in entries)
        assert counts == row["dispositions"]
        assert row["additional_measurement_projections"] == counts["measurements"] + counts["partial_parse"]
        for entry in entries:
            sha = entry["source_sha256"]
            assert re.fullmatch("[a-f0-9]{64}",sha) and re.fullmatch("[a-f0-9]{64}",entry["artifact_id"])
            if entry["status"] not in {"measurements","partial_parse"}:
                assert "file" not in entry
                continue
            assert row["version"] in entry["versions"]
            path = folder / entry["file"]
            assert path == folder / "records" / sha[:2] / (sha+".json.gz")
            if path in files:
                continue
            files.add(path)
            value = read_gzip(path)
            if isinstance(value,list) and value and isinstance(value[0],dict) and set(value[0])=={"line","measurements"}:
                assert all(set(item)=={"line","measurements"} and type(item["line"]) is int and item["measurements"]==numeric_project(item["measurements"]) for item in value)
            else:
                assert value == numeric_project(value)
    assert files == set((folder/"records").glob("*/*.json.gz"))
    known = {a:v for v,a in RUNS.items()}
    streams = {}
    for stream in rows(folder/"case-streams.jsonl.gz"):
        aid = stream["artifact_id"]
        assert aid not in streams
        streams[aid] = stream
    actual = Counter()
    selected = defaultdict(dict)
    for row in rows(out/"case-records.jsonl.gz"):
        aid = row["artifact_id"]
        actual[aid] += 1
        if aid in known:
            p = row["projection"]["judgment"]
            key = row["case_key"]
            assert key not in selected[aid]
            selected[aid][key] = (p.get("semantic_judge_label"), p["semantic_judge_status"], p["e2e_pass"])
    assert actual == {aid:r["counts"]["rows"] for aid,r in streams.items()}
    manifest = json.loads((folder/"manuscript-runs.json").read_text())
    for v,aid in RUNS.items():
        stream = list(rows(folder/(v+".jsonl.gz")))
        assert len(stream)==len(selected[aid])==2000
        assert all(set(r)=={"case_key","semantic_label","judge_status","e2e_pass"} for r in stream)
        assert {r["case_key"]:(r["semantic_label"],r["judge_status"],r["e2e_pass"]) for r in stream} == selected[aid]
        assert manifest[v] == streams[aid]
        strict = sum(r["semantic_label"] in {"correct","correct_refusal"} for r in stream)
        partial = sum(r["semantic_label"]=="partial" for r in stream)
        assert (strict,partial)=={"v1222":(1513,328),"v1225":(1590,253),"v1226":(1517,349),"v1227":(1542,279),"v1371":(1550,315)}[v]
    print("Verified version dispositions:",dict(statuses),"unique numerical projections:",len(files),"case streams:",len(streams))


if __name__ == "__main__":
    verify(Path(__file__).resolve().parents[1] / "evidence")
