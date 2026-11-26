"""Extract allowlisted measurements from archived members and structured log lines."""
import argparse
from collections import Counter
import io
import json
from pathlib import Path
import tarfile
import zipfile

from build_review_evidence import has_measurement, numeric_project
from export_evidence import ROOTS, compressed, digest, emit, versions
from recover_version_evidence import FORMATS, files, measurements


LOGS = {".txt", ".log", ".stdout", ".stderr"}


def inspect(raw, suffix):
    if suffix in FORMATS:
        return measurements(raw, suffix)
    found = []
    for line, segment in enumerate(io.BytesIO(raw), 1):
        if not segment.lstrip().startswith((b"{", b"[")):
            continue
        try:
            parsed = numeric_project(json.loads(segment))
        except (ValueError, UnicodeError, RecursionError):
            continue
        if has_measurement(parsed):
            found.append({"line":line, "measurements":parsed})
    return found or None, 0


def members(path):
    if path.suffix.lower() in LOGS:
        yield "", path.suffix.lower(), path.read_bytes()
    elif path.suffix == ".zip":
        with zipfile.ZipFile(path) as archive:
            for info in archive.infolist():
                suffix = Path(info.filename).suffix.lower()
                if not info.is_dir() and suffix in FORMATS | LOGS:
                    yield info.filename, suffix, archive.read(info)
    else:
        with tarfile.open(path) as archive:
            for info in archive:
                suffix = Path(info.name).suffix.lower()
                if info.isfile() and suffix in FORMATS | LOGS:
                    with archive.extractfile(info) as handle:
                        yield info.name, suffix, handle.read()


def export(source, backup, out):
    folder = out / "version-recovery"
    coverage = Counter()
    with compressed(folder/"embedded-sources.jsonl.gz") as output:
        roots = [(source/x, source, "checkout") for x in ROOTS]
        roots += [(x, backup, "separate_archive") for x in sorted(backup.glob("v[0-9]*"))]
        for root, base, origin in roots:
            for path in files(root):
                rel = path.relative_to(base).as_posix()
                vs = versions(rel)
                if not vs or not (path.suffix.lower() in LOGS or path.name.endswith((".tar.gz",".tgz",".zip"))):
                    continue
                key = ("archive/" if origin=="separate_archive" else "") + rel
                coverage["scanned_files"] += 1
                parent_sha = None
                for name, suffix, raw in members(path):
                    try:
                        value, invalid = inspect(raw,suffix)
                    except (ValueError, UnicodeError, OverflowError, RecursionError):
                        value, invalid = None, 1
                    sha = digest(raw)
                    state = "no_allowlisted_measurements" if value is None else "measurements"
                    if invalid:
                        state = "parse_error" if value is None else "partial_parse"
                    row = {"artifact_id":digest((key + ("!/"+name if name else "")).encode()),
                           "source_sha256":sha, "origin":origin, "versions":vs,
                           "status":state, "input_format":"archive_member" if name else "log_text"}
                    if name:
                        if parent_sha is None:
                            from export_evidence import stream_hash
                            parent_sha = stream_hash(path)
                        row["container_sha256"] = parent_sha
                    if invalid:
                        row["invalid_records"] = invalid
                    if value is not None:
                        dest = folder/"records"/sha[:2]/(sha+".json.gz")
                        if not dest.exists():
                            with compressed(dest) as stream:
                                emit(stream,value)
                        row["file"] = dest.relative_to(folder).as_posix()
                    emit(output,row)
                    coverage[state] += 1
    print(dict(coverage))


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source",type=Path,required=True)
    parser.add_argument("--backup",type=Path,required=True)
    parser.add_argument("--output",type=Path,default=Path("evidence"))
    args=parser.parse_args()
    export(args.source,args.backup,args.output)
