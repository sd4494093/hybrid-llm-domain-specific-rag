# Iteration History and Evidence Coverage

This is an exhaustive index of version identifiers v1 through v1660 within the
declared local evidence scope. It is not a claim of 1,660 complete experiments,
1,660 successful improvements, or a single unchanged evaluation cohort.

## Coverage

Files inventoried: 155,386. Structured summaries: 8,676.
Public case records: 474,340. Versions with located references: 1490/1660.
Versions without located references: 170.

- [v1 to v100](history/v0001-v0100.md)
- [v101 to v200](history/v0101-v0200.md)
- [v201 to v300](history/v0201-v0300.md)
- [v301 to v400](history/v0301-v0400.md)
- [v401 to v500](history/v0401-v0500.md)
- [v501 to v600](history/v0501-v0600.md)
- [v601 to v700](history/v0601-v0700.md)
- [v701 to v800](history/v0701-v0800.md)
- [v801 to v900](history/v0801-v0900.md)
- [v901 to v1000](history/v0901-v1000.md)
- [v1001 to v1100](history/v1001-v1100.md)
- [v1101 to v1200](history/v1101-v1200.md)
- [v1201 to v1300](history/v1201-v1300.md)
- [v1301 to v1400](history/v1301-v1400.md)
- [v1401 to v1500](history/v1401-v1500.md)
- [v1501 to v1600](history/v1501-v1600.md)
- [v1601 to v1660](history/v1601-v1660.md)

## Reading the Evidence

Each version links to source artifact IDs, summary IDs, document event IDs, and
Git commit hashes. Path and prose mentions may refer to an older comparator or
an oracle/schema version; they do not establish tested code identity. The
document events retain line numbers, line hashes, dates, and reported numeric
tokens. Those tokens are unverified statements until linked to a result.

`inventory.jsonl.gz` contains an entry for every regular file found in the
declared roots. `summaries.jsonl.gz`, `case-records.jsonl.gz`, and
`document-events.jsonl.gz` contain conservative public projections. Source paths
are represented by SHA-256 IDs to avoid disclosing internal names. Recompute an
ID from the UTF-8 repository-relative POSIX path using SHA-256. Original file
hashes bind projections to the private source. Public file hashes are listed in
`public-manifest.json` after verification.

## Verified Anchors

- [MVP UAT](baseline-UAT-20260608/README.md): 2,000 aggregated runs; combined
  evaluation resolves two initial Judge errors. 1,204 correct, 587 partial,
  172 incorrect, 37 refusal. Usefulness is 1,791/2,000 = 89.55%.
- [v1660](v1660-final-baseline/README.md): natural-user 2,000-case cohort,
  semantic correctness 1,451/2,000 = 72.55%, including 396 correct refusals;
  strict E2E 1,422/2,000 = 71.10%. The 85% semantic target is not reached.
- v1441: the v1660 promotion decision identifies 1,435/2,000 as its comparator.
  The accepted change is +16 cases (+0.80 percentage points). This does not
  imply every case improved or statistical significance.
- Other full-cohort summaries, including rejected candidates and intermediate
  aggregation states, are indexed in `full-cohort-summary-candidates.json`.
  They require matching question, oracle, source, model and evaluator contracts
  before comparison. A higher earlier score is not automatically a better
  candidate under a changed evaluation contract.

## Corrections to the Draft History

The earlier draft's v100/55%, v500/65%, v1000/70% milestones had no cited
evidence and are withdrawn. The 411 planner/partial cases are an owning-layer
failure bucket, not a separately validated usefulness label. The claimed 93.1%
usefulness, zero refusal, and 138 total failures are withdrawn. Local dev
acceptance as an iteration baseline is not production acceptance. No June to
September causal quality-gate improvement is inferred from unequal protocols.

## Scope and Reproduction

See [coverage.json](coverage.json), [export policy](validation-protocols/export-policy.md),
and [evaluation protocol](validation-protocols/semantic-judge-protocol.md).
Use `python tools/export_evidence.py --source /path/to/private/repository`
to rebuild from the private evidence tree. Missing or withheld artifacts remain
explicit limitations. This public release reproduces aggregate calculations,
not the proprietary corpus, runtime deployment, or independent semantic grading.
