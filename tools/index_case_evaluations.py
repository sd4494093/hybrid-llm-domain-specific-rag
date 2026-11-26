"""Index every archived case stream, keeping source files and reruns separate."""
import argparse
from collections import Counter
import gzip
import itertools
import json
from pathlib import Path

from export_evidence import compressed, dump, emit
from recover_version_evidence import RUNS
from build_review_evidence import artifact_dir, rows


def build(out):
    folder = out / "version-recovery"
    lookup = {v:k for k,v in RUNS.items()}
    with gzip.open(out/"inventory.jsonl.gz","rt") as stream:
        inv = {r["artifact_id"]:r for r in map(json.loads,stream) if r.get("exported_rows")}
    runs = {}
    full_streams = []
    with compressed(folder/"case-streams.jsonl.gz") as catalog:
        for aid,group in itertools.groupby(rows(out/"case-records.jsonl.gz"),lambda r:r["artifact_id"]):
            counts = Counter()
            cases = set()
            selected = []
            for r in group:
                counts["rows"] += 1
                cases.add(r["case_key"])
                p = r["projection"].get("judgment",r["projection"])
                label = p.get("semantic_judge_label",p.get("label"))
                status = p.get("semantic_judge_status",p.get("evaluator_status"))
                if label:
                    counts[label] += 1
                if status == "error":
                    counts["judge_errors"] += 1
                if type(p.get("e2e_pass")) is bool:
                    counts["e2e_observed"] += 1
                    counts["e2e_passed"] += p["e2e_pass"]
                if aid in lookup:
                    if not (status == "error" and label is None or status in {"ok","uncertain"} and label in {"correct","correct_refusal","partial","incorrect","incorrect_refusal","uncertain"}):
                        raise ValueError("Unexpected judgment in selected evaluation")
                    selected.append({"case_key":r["case_key"],"semantic_label":label,"judge_status":status,"e2e_pass":p["e2e_pass"]})
            original = inv[aid]
            assert counts["rows"] == original["exported_rows"]
            record = {"artifact_id":aid,"source_sha256":original["source_sha256"],"version_mentions":original["version_mentions"],
                      "distinct_case_keys":len(cases),"counts":dict(counts)}
            if selected:
                v = lookup[aid]
                assert len(cases)==len(selected)==counts["e2e_observed"]==2000
                with compressed(folder/(v+".jsonl.gz")) as stream:
                    for row in selected:
                        emit(stream,row)
                runs[v] = record
            if counts["rows"] == 2000:
                full_streams.append(record)
            emit(catalog,record)
    assert runs.keys()==RUNS.keys()
    page = out/"FULL_COHORT_EVALUATIONS.md"
    original_table = page.read_text().split("| Referenced versions | Artifact |",1)[1]
    table = ["# Full-Cohort Evaluation Inventory","","## Manuscript runs under judge protocol v5","",
             "The earlier inventory selected projected summary files with a question count of 2,000 and a quality-metrics object. The older evaluations have case verdicts even when that object is absent. The previous supplement flag governed additional numerical extraction; the archived JSONL verdicts were already public under artifact IDs. A version mention may denote a comparator or schema revision. The executing version in each row below was matched to the archived run settings.","",
             "| Executing version | Archived under | Cases | Strict | Partial | Strict or partial | E2E pass | Judge errors | Uncertain | Released case records | Original paginated projection |",
             "|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|"]
    for v in RUNS:
        r = runs[v]
        c = Counter(r["counts"])
        strict = c["correct"] + c["correct_refusal"]
        artifact = artifact_dir(out,r["artifact_id"])/"README.md"
        table.append(f"| {v} | {'v1408' if v=='v1371' else v} | 2,000 | {strict:,} | {c['partial']} | {strict+c['partial']:,} | {c['e2e_passed']:,} | {c['judge_errors']} | {c['uncertain']} | [Download](version-recovery/{v}.jsonl.gz) | [{r['artifact_id'][:12]}]({artifact.relative_to(out)}) |")
        for path in [artifact, *[p for n in set(r["version_mentions"]) for p in (out/"review").glob(f"v*-v*/v{n:04}/artifacts-*.md")]]:
            lines = path.read_text().splitlines(keepends=True)
            for i,line in enumerate(lines):
                if path==artifact and "Supplement:" in line or path!=artifact and r["artifact_id"] in line:
                    lines[i]=line.replace("not_selected_for_supplement","published case records (original projection)")
            path.write_text("".join(lines))
    table += ["","Strict counts correct answers plus correct refusals. Errors and uncertain judgments remain in the denominator. For v1225 the 1,589 end-to-end passes and 1,590 strictly correct labels measure different outcomes. See the [run settings](audit-feedback/run-settings.json) and the [all-version recovery index](version-recovery/README.md).","","## Historical summary candidates","","These rows describe individual summary artifacts, including intermediate and rejected results. Match provenance before comparing or combining counts.","","| Referenced versions | Artifact |"+original_table]
    page.write_text("\n".join(table))
    groups = ["# Archived streams with 2,000 observed rows", "",
              "These are physical files, including overlapping runtime, evaluation, judge, and retry streams. Version columns are path mentions. A missing semantic label count is unreported. Strict counts below require every observed row to have either a recognized semantic outcome or a judge error. The original case archive can be filtered by the full artifact ID.", "",
              "| Version mentions | Distinct case keys | Strict | Partial | E2E pass | Artifact ID |",
              "|---|---:|---:|---:|---:|---|"]
    labels = ("correct", "correct_refusal", "partial", "incorrect", "incorrect_refusal", "uncertain")
    for r in full_streams:
        c = Counter(r["counts"])
        scored = sum(c[k] for k in labels) + c["judge_errors"] == c["rows"]
        strict = c["correct"] + c["correct_refusal"] if scored else "unreported"
        partial = c["partial"] if scored else "unreported"
        e2e = c["e2e_passed"] if c["e2e_observed"] == c["rows"] else "unreported"
        aid = r["artifact_id"]
        browse = artifact_dir(out,aid)/"README.md"
        target = f"[{aid}]({browse.relative_to(out)})" if browse.exists() else aid
        mentions = ", ".join(f"v{n}" for n in r["version_mentions"]) or "unattributed"
        groups.append(f"| {mentions} | {r['distinct_case_keys']} | {strict} | {partial} | {e2e} | {target} |")
    (out/"FULL_LENGTH_CASE_STREAMS.md").write_text("\n".join(groups)+"\n")
    marker = "## Historical summary candidates"
    v6_links = "The conventional control (1,318 strictly correct) and v1660 (1,451 strictly correct) use judge protocol v6. See the [control case labels](baseline-system-evaluation/case-labels.json) and [v1660 case labels](proposed-system-evaluation/case-labels.json). The case-level v1222 labels give 1,513 strict; the separately indexed 1,512-count summary below is retained as its own artifact.\n\n"
    page.write_text(page.read_text().replace(marker, v6_links + "[All archived streams with 2,000 rows](FULL_LENGTH_CASE_STREAMS.md)\n\n"+marker,1))
    dump(folder/"manuscript-runs.json",runs)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,default=Path("evidence"))
    build(parser.parse_args().output)
