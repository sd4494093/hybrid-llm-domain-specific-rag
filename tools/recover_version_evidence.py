"""Reconcile version-associated public records with the private evidence roots."""
import argparse
from collections import Counter, defaultdict
import csv
import gzip
import io
import json
import os
from pathlib import Path
import subprocess

from build_review_evidence import has_measurement, numeric_project, scalar, stream_project, version_dir
from export_evidence import ROOTS, SKIP_DIRS, compressed, digest, dump, emit, stream_hash, versions


FORMATS = {".json", ".jsonl", ".csv", ".tsv", ".exit", ".exit_status"}
RUNS = {
    "v1222": "df2346c5d13bc94c98de369901521a517532dfcd1a0651248f0a74222d93da3c",
    "v1225": "e2701d154f4f55809b19d5056283d9c210c0bf9fe2ba090a16208c16514ff7a3",
    "v1226": "6346324b5a1fc21d8fa89a0d7e82cd885e66da2283da11bec5dfdb7f63da96d8",
    "v1227": "67b3baac8a46a29c9cc20a27cb88f96c62b795a0376a6c03ee4a2b1223ff6ab8",
    "v1371": "ea2e69deceb2669f3fc046adce6f1caf95f2e76d58de03193a4524b50d719e13",
}


def measurements(data, ext):
    if ext == ".json":
        value = stream_project(io.BytesIO(data))
        return value if has_measurement(value) else None, 0
    if ext in (".exit", ".exit_status"):
        return {"exit_code": int(data.strip())}, 0
    result = []
    invalid = 0
    if ext == ".jsonl":
        for line, raw in enumerate(io.BytesIO(data), 1):
            if not raw.strip():
                continue
            try:
                value = numeric_project(json.loads(raw))
            except (ValueError, UnicodeError):
                invalid += 1
                continue
            if has_measurement(value):
                result.append({"line": line, "measurements": value})
    else:
        reader = csv.DictReader(io.StringIO(data.decode("utf-8-sig")), delimiter="," if ext == ".csv" else "\t")
        for line, row in enumerate(reader, 2):
            value = {}
            for key, raw in row.items():
                try:
                    parsed = json.loads(raw)
                except (TypeError, ValueError):
                    parsed = raw
                keep, val = scalar(key, parsed)
                if keep:
                    value[key] = val
            if value:
                result.append({"line": line, "measurements": value})
    return result or None, invalid


def files(root):
    for parent, dirs, names in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS and not d.startswith("paper-baseline-")
                         and not (Path(parent) / d).is_symlink())
        for name in sorted(names):
            path = Path(parent) / name
            if not path.is_symlink() and path.is_file():
                yield path


def export(source, backup, out):
    folder = out / "version-recovery"
    folder.mkdir(exist_ok=True)
    with gzip.open(out / "inventory.jsonl.gz", "rt") as stream:
        inventory = {r["artifact_id"]: r for r in map(json.loads, stream) if r["version_mentions"]}
    status = json.loads((out / "review/artifact-status.json").read_text())
    counters = defaultdict(Counter)
    extra = defaultdict(list)
    observed = set()
    seen = set()
    data_dir = folder / "records"

    def recover(rel, vs, ext, read, origin):
        aid = digest(rel.encode())
        old = inventory.get(aid)
        if old and origin == "checkout":
            observed.add(aid)
        if ext not in FORMATS:
            return
        if old and origin == "checkout":
            meta = status[aid]
            if meta["supplement"] == "numeric_content" or meta["case_rows"]:
                return
        raw = read()
        sha = digest(raw)
        if (aid, sha) in seen:
            return
        seen.add((aid, sha))
        if old and origin == "git_history" and sha == old["source_sha256"] and (
                status[aid]["supplement"] == "numeric_content" or status[aid]["case_rows"]):
            return
        record = {"artifact_id": aid, "source_sha256": sha, "origin": origin, "versions": vs}
        if old and old["source_sha256"] != sha:
            record["original_snapshot_sha256"] = old["source_sha256"]
        try:
            value, invalid = measurements(raw, ext)
        except (ValueError, UnicodeError, csv.Error, OverflowError, StopIteration, RecursionError):
            value, invalid = None, 1
        state = "measurements" if value is not None else "no_allowlisted_measurements"
        if invalid:
            state = "partial_parse" if value is not None else "parse_error"
            record["invalid_records"] = invalid
        record["status"] = state
        if value is not None:
            dst = data_dir / sha[:2] / (sha + ".json.gz")
            if not dst.exists():
                with compressed(dst) as stream:
                    emit(stream, value)
            record["file"] = dst.relative_to(folder).as_posix()
        for v in vs:
            extra[v].append(record)
            counters[v][state] += 1

    for root in ROOTS:
        for p in files(source / root):
            rel = p.relative_to(source).as_posix()
            vs = versions(rel)
            if vs:
                recover(rel, vs, p.suffix.lower(), p.read_bytes, "checkout")
    for root in sorted(backup.glob("v[0-9]*")):
        for p in files(root):
            rel = p.relative_to(backup).as_posix()
            vs = versions(rel)
            if vs:
                recover("archive/" + rel, vs, p.suffix.lower(), p.read_bytes, "separate_archive")
    # Inspect reachable revisions, including files deleted from the working tree.
    history = subprocess.check_output(["git", "-C", str(source), "log", "--all", "--no-renames",
                                      "--raw", "--no-abbrev", "--format=", "-z", "--", *ROOTS])
    fields = iter(history.split(b"\0"))
    blobs = set()
    for field in fields:
        if not field.strip():
            continue
        meta = field.strip().split()
        rel = os.fsdecode(next(fields))
        vs = versions(rel)
        if not vs or any(x.startswith("paper-baseline-") for x in Path(rel).parts):
            continue
        for mode, blob in zip([meta[0][1:], meta[1]], meta[2:4]):
            if mode in (b"100644", b"100755") and (rel, blob) not in blobs:
                blobs.add((rel, blob))
                recover(rel, vs, Path(rel).suffix.lower(), lambda: subprocess.check_output(
                    ["git", "-C", str(source), "cat-file", "blob", blob]), "git_history")
    for aid in inventory.keys() - observed:
        old = inventory[aid]
        if old["suffix"] in FORMATS and not status[aid]["case_rows"] and status[aid]["supplement"] != "numeric_content" and (aid, old["source_sha256"]) not in seen:
            for v in old["version_mentions"]:
                extra[v].append({"artifact_id": aid, "source_sha256": old["source_sha256"], "status": "original_bytes_unlocated"})
                counters[v]["original_bytes_unlocated"] += 1
    index = []
    for v in range(1, 1661):
        old = json.loads((out / "iterations" / f"v{v:04}.json").read_text())
        previous = sum(bool(set(status[a]["content"]) & {"summary","case_records","numeric_content"}) for a in old["artifact_ids"])
        records = sorted(extra[v], key=lambda r:(r["artifact_id"],r["source_sha256"]))
        directory = version_dir(out,v)
        details = folder / "versions" / directory.parent.name / f"v{v:04}.json.gz"
        with compressed(details) as stream:
            emit(stream, records)
        measured = counters[v]["measurements"] + counters[v]["partial_parse"]
        outcome = "measured" if previous or measured else "archive_references_only" if old["artifact_ids"] or old["document_events"] or old["commit_ids"] or records else "no_located_reference"
        index.append({"version":v,"status":outcome,"existing_measured_artifacts":previous,"additional_measurement_projections":measured,
                      "dispositions":dict(counters[v]),"details":details.relative_to(folder).as_posix()})
        page = directory / "README.md"
        before = page.read_text().split("\n## Additional recovered evidence\n")[0].rstrip()
        page.write_text(before + "\n\n## Additional recovered evidence\n\n" + f"Status: `{outcome}`. {measured} additional numerical projections. [Source dispositions and download paths]({os.path.relpath(details,directory)}) · [Coverage guide]({os.path.relpath(folder/'README.md',directory)}).\n")
    dump(folder/"versions.json",index)
    print(Counter(r["status"] for r in index),flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True,type=Path)
    parser.add_argument("--backup", required=True,type=Path)
    parser.add_argument("--output", default=Path("evidence"),type=Path)
    args = parser.parse_args()
    export(args.source.resolve(strict=True),args.backup.resolve(strict=True),args.output)
