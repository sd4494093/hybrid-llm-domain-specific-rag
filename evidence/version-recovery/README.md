# Version evidence recovery

This release audits v1 through v1660. The unit below is a version identifier. A measured version has at least one path-associated summary, case record, or numerical projection. Probes, incomplete runs, retries, and comparator mentions can all produce evidence. Completion and deployment require separate run-level evidence.

| Status | Versions |
|---|---:|
| measured | 1442 |
| archive_references_only | 48 |
| no_located_reference | 170 |

## Download and recount

The [version index](versions.json) has one row per identifier. Each row links to a compressed JSON list of source dispositions. Within that list, each measurement file path is relative to this directory. Artifact IDs identify source paths by hash. Source SHA-256 identifies exact bytes. Historical variants have their own fingerprints. Sources with identical bytes share a measurement download.

The [case-stream catalog](case-streams.jsonl.gz) indexes every original case stream by artifact ID. It reports observed rows, distinct case keys, label counts, and the number of rows with an end-to-end verdict. To retrieve the projected records for a catalog entry, filter the [original archive](../case-records.jsonl.gz) by artifact_id. Multiple streams can describe the same questions, retries or intermediate judgments. Do not add their counts as distinct cases.

The [full-cohort inventory](../FULL_COHORT_EVALUATIONS.md) identifies five v5 manuscript runs and links to 2,000 pseudonymous verdicts per run. The conventional control and v1660 have separate case releases under the same inventory. The [historical document index](additional-document-mentions.jsonl.gz) provides source and line fingerprints with version mentions. It contains no document text.

The structured scan covers JSON, JSONL, CSV, TSV and exit status files with explicit version associations within the original five private evidence roots, reachable Git revisions of those paths, and the separate versioned backups. The aligned conventional control has its own [release](../baseline-system-evaluation/README.md). The previously retired control is excluded. Earlier allowlisted results and the original inventory are preserved. Sources outside that scope (including private enterprise documents and unstructured logs or images) are not released as outcome data.

The [embedded source index](embedded-sources.jsonl.gz) also covers structured members of located version-associated ZIP and tar archives and JSON-formatted lines in text or log files. Only allowlisted measurements are released. Missing, malformed or unprojectable structured sources have explicit dispositions. For a partially parseable JSONL file, valid measurements retain their original line numbers, and the disposition records the invalid-line count. Where only a fingerprint or document/commit mention survives, run completion and its outcome are unknown. Missing rows carry no assumed label or score.

## Browse by version

- [v0001-v0050](v0001-v0050.md)
- [v0051-v0100](v0051-v0100.md)
- [v0101-v0150](v0101-v0150.md)
- [v0151-v0200](v0151-v0200.md)
- [v0201-v0250](v0201-v0250.md)
- [v0251-v0300](v0251-v0300.md)
- [v0301-v0350](v0301-v0350.md)
- [v0351-v0400](v0351-v0400.md)
- [v0401-v0450](v0401-v0450.md)
- [v0451-v0500](v0451-v0500.md)
- [v0501-v0550](v0501-v0550.md)
- [v0551-v0600](v0551-v0600.md)
- [v0601-v0650](v0601-v0650.md)
- [v0651-v0700](v0651-v0700.md)
- [v0701-v0750](v0701-v0750.md)
- [v0751-v0800](v0751-v0800.md)
- [v0801-v0850](v0801-v0850.md)
- [v0851-v0900](v0851-v0900.md)
- [v0901-v0950](v0901-v0950.md)
- [v0951-v1000](v0951-v1000.md)
- [v1001-v1050](v1001-v1050.md)
- [v1051-v1100](v1051-v1100.md)
- [v1101-v1150](v1101-v1150.md)
- [v1151-v1200](v1151-v1200.md)
- [v1201-v1250](v1201-v1250.md)
- [v1251-v1300](v1251-v1300.md)
- [v1301-v1350](v1301-v1350.md)
- [v1351-v1400](v1351-v1400.md)
- [v1401-v1450](v1401-v1450.md)
- [v1451-v1500](v1451-v1500.md)
- [v1501-v1550](v1501-v1550.md)
- [v1551-v1600](v1551-v1600.md)
- [v1601-v1650](v1601-v1650.md)
- [v1651-v1660](v1651-v1660.md)
