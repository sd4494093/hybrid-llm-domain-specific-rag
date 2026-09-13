# Evidence Browser Repair

## Problems Confirmed

The original summary exporter selected JSON filenames containing `summary`,
`provenance`, `decision`, or `manifest`. It did not project array contents.
Consequently, numerical `results.json` probes such as the two v1617 artifacts
were inventoried but not published as readable test results. Per-case JSONL
verdicts existed in a global compressed archive but were not reachable from
individual version pages. These were distinct from genuinely missing sources.

The legacy directory also contains 1,660 version folders. GitHub truncates
the directory listing at 1,000 entries; "660 entries not shown" is a browser
limit, not evidence that those folders were absent from Git.

## Repair Scope

- All 1,660 version identifiers have range navigation, at most 50 per range.
- All path-associated artifacts have a disposition and a direct data link.
- Existing summaries and JSONL case verdicts are expanded without changing
  labels, source fingerprints, order, or retry records.
- Supplemental JSON and previously unprojected JSONL are examined for
  v1000-v1660, regardless of filename. Streaming JSON parsing removes the
  original 16 MiB selection limit without retaining private answer text.
- Allowlisted nested numerical arrays preserve order, false flags and missing
  ranks. Empty placeholders mean omitted content, not success. Private case,
  parent, segment and dataset IDs are not added to the supplement.
- Large arrays are split into at most 50 rows per JSON page. Each data page is
  bounded to 192 KiB and its directory is sharded. Page paths inside JSON are
  relative to the source artifact or version directory, with Markdown links
  provided in adjacent page indexes.
- Source bytes must match the original inventory. Missing, changed, malformed,
  or unprojectable sources remain explicit gaps.

Use the [browser](../evidence/review/README.md) and
[machine-readable coverage](../evidence/review/coverage.json). The historical
version URLs are preserved, with a prominent link to the new content.

## Published Coverage

The supplement contains 5,222 numerical source projections, while the readable
browser expands 399,300 existing version-associated case records. It provides
dispositions for all 62,778 version-associated inventory files. These counts
include overlapping artifacts and metadata, not independent experiments.

For v1000-v1660, 531 of 661 identifiers have numerical summaries, probes, or case
verdicts. The other 130 are still not backed by public numerical results:
72 have no references in the declared inventory, ten have only document/commit
mentions, and 48 have path-associated fingerprint/event-only artifacts. These
are visible on the range pages; this repair does not claim 1,660 complete tests.

Among supplemental source candidates, 537 contain no allowlisted measurements
and four fail strict JSON/JSONL parsing. Inspection confirmed an empty file,
invalid JSON outputs, and a multi-line object stream mislabeled as JSONL. Those
inputs remain fingerprint-only rather than being repaired or interpreted as
successful test runs. No selected source was silently replaced by newer bytes.

## Interpretation Limits

This is a public numerical evidence package, not a release of private questions,
answers, rationales, screenshots, or complete runtime traces. A source fingerprint
alone is not evidence of a test outcome. Version mentions may denote comparators
or schema versions. Case rows can include retries and overlapping runs; neither
row counts nor version identifiers count independent experiments.

The two v1617 sources are small candidate-selection probes, not 2,000-question
accuracy evaluations. Their first case records vector rank 57 with a candidate
limit of 50 and `expected_in_candidates=false`. This is a recorded diagnostic
observation, not proof of a global accuracy change or a causal explanation of
every retrieval failure.

No paper metrics, baseline definitions, or architecture claims are changed by
this repair. The original inventory and global archives remain unchanged.
The earlier rename to `baseline-system-evaluation` and
`proposed-system-evaluation` had left stale documentation links and recomputation
paths. Those references and generator destinations are updated to the existing
directory names; the strict numerator still includes the 396 correct refusals.

## Verification

`tools/verify_review_evidence.py` reconstructs every paginated record and checks
it against original summaries, case records, events, commits, and source hashes.
It checks supplemental allowlists, complete artifact disposition coverage, page
limits and directory limits. `tools/verify_evidence.py` invokes it and also checks
repository links, sensitive markers, aggregate arithmetic, and release hashes.

Private-source export additionally requires the pinned streaming JSON parser
in `tools/requirements-export.txt`. Public verification uses the standard library.
