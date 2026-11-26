"""Add explicitly versioned historical document lines to the recovery index."""
from collections import Counter, defaultdict
import json
import os
from pathlib import Path
import subprocess

from export_evidence import ROOTS, compressed, digest, emit, versions
from build_review_evidence import rows
from recover_version_evidence import files


def build(source, backup, out):
    old = {r["artifact_id"]: r for r in rows(out/"inventory.jsonl.gz") if r["suffix"]==".md"}
    seen = set()
    counts = Counter()
    folder = out/"version-recovery"
    def record(rel, raw, origin, output):
        sha = digest(raw)
        aid = digest(rel.encode())
        if (aid,sha) in seen:
            return
        seen.add((aid,sha))
        prev = old.get(aid,{})
        if prev.get("source_sha256")==sha and prev.get("disposition")=="document_event_projection":
            return
        for line, data in enumerate(raw.splitlines(),1):
            vs = versions(data.decode("utf8","replace"))
            if vs:
                emit(output,{"artifact_id":aid,"source_sha256":sha,"line":line,"line_sha256":digest(data),
                             "version_mentions":vs,"origin":origin})
                counts.update(vs)
    with compressed(folder/"additional-document-mentions.jsonl.gz") as output:
        for root in ROOTS:
            for path in files(source/root):
                if path.suffix.lower()==".md":
                    record(path.relative_to(source).as_posix(),path.read_bytes(),"checkout",output)
        for root in sorted(backup.glob("v[0-9]*")):
            for path in files(root):
                if path.suffix.lower()==".md":
                    record("archive/"+path.relative_to(backup).as_posix(),path.read_bytes(),"separate_archive",output)
        history=subprocess.check_output(["git","-C",str(source),"log","--all","--no-renames","--raw","--no-abbrev","--format=","-z","--",*ROOTS])
        fields=iter(history.split(b"\0"))
        done=set()
        for field in fields:
            if not field.strip():
                continue
            meta=field.strip().split()
            rel=os.fsdecode(next(fields))
            if not rel.lower().endswith(".md") or any(part.startswith("paper-baseline-") for part in Path(rel).parts):
                continue
            for mode,oid in zip([meta[0][1:],meta[1]],meta[2:4]):
                if mode in (b"100644",b"100755") and (rel,oid) not in done:
                    done.add((rel,oid))
                    record(rel,subprocess.check_output(["git","-C",str(source),"cat-file","blob",oid]),"git_history",output)
    print("Additional document mentions for",len(counts),"versions")


if __name__=="__main__":
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source",type=Path,required=True)
    parser.add_argument("--backup",type=Path,required=True)
    parser.add_argument("--output",type=Path,default=Path("evidence"))
    args=parser.parse_args()
    build(args.source,args.backup,args.output)
