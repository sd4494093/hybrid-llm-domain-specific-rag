# Public Evidence Export Policy

The export scans regular files under `.playwright`, `.ralph`, `tests/e2e`,
`tmp`, and `doc/dify_dev` in the private repository. Git metadata covers all
reachable commits. Symlinks and environment/dependency directories are skipped.
This is a working-tree archive, not a dump of every blob in Git history.

## Included

- SHA-256, size, extension category and disposition for each inventoried file.
- Whitelisted numeric aggregate fields, exact known status/label values,
  model configuration identifiers and provenance hashes in selected JSON files.
- Whitelisted per-case verdicts, booleans, scores and hashes in JSONL result,
  judgment, failure and verdict files; pseudonymous case keys preserve joins.
- Markdown event line numbers, line hashes, heading dates, version mentions,
  numeric ratio/percentage tokens and fixed decision tokens.
- Git commit hashes, dates, subject hashes and version mentions.

The exporter associates files with every version mentioned in the path. It
does not infer which version produced the file. Reports may mention a previous
baseline, an oracle/schema version or several candidates. Markdown numerical
tokens are reported statements, not interpreted experimental measurements.

## Withheld

Raw questions, answers, rationales, source excerpts, document names and URLs,
email addresses, credentials, screenshots, browser storage, trace payloads,
embeddings and database exports are never copied. Unknown JSON keys and values
are omitted by default. Original paths are replaced by their SHA-256 IDs.
Some files contribute only a hash. Count-only projection loses explanatory
context, so an independent reviewer needs controlled private access to examine
source facts or re-grade answers. Hashes are fingerprints, not signatures or
proof that the original experiment was correctly conducted.

Per-case keys hash the tuple of the private run partition and original case ID.
They are stable pseudonyms, not guaranteed anonymization against an informed
party. The public release contains no regional comparison table.

JSON summary candidates larger than 16 MiB and Markdown files larger than
4 MiB remain hash-only. JSONL records are processed line-by-line. Invalid rows,
read errors and files changed during export are counted. All original files,
including those excluded from content projection, remain inventoried.

## Readable Supplement

The [paginated browser](../review/README.md) expands existing public case records
and summaries without modifying the original archive. Its supplemental exporter
examines all inventoried JSON and previously unprojected JSONL associated with
v1000-v1660, including `results.json` and large files omitted by the older filter.
Streaming parsing retains only explicit numeric, Boolean, enum and hash fields
inside allowlisted containers. Lists preserve positions; null ranks and false
flags remain visible. No raw dataset, parent, segment or case IDs are added.

Every source must match its inventoried SHA-256 before supplemental content is
published. Missing, changed, unparseable, and unprojectable inputs have explicit
dispositions. Other private formats remain fingerprint/event-only, not fabricated
results. Coverage counts distinguish test-content artifacts from references.

## Release Verification

`tools/verify_evidence.py` parses every compressed record, enforces the projection
allowlist, verifies cross-references and label totals, checks a denylist of
sensitive markers in evidence text, and validates public file hashes. This is
a technical minimization check, not a substitute for source-owner disclosure
review. The release makes no claim to disclose all original private evidence.

Regeneration is deterministic for an unchanged tree and commit set. The
private checkout is read-only. The public manifest excludes itself and can be
rebuilt using `--write-manifest`; normal verification rejects changed files.
