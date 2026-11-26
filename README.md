# Dual-Layer Domain-Specific RAG with Audit Feedback — Evaluation Archive

Companion evidence for the manuscript by Junjie Wang and Lihong Zheng.
This repository lets a reader inspect and recount the evaluations reported in the paper.
It is not a deployment package, and publication acceptance is not claimed.

**Data snapshot:** commit `6299e8ecc` · 2,000-case verdicts for every reported full-cohort run · all 1,660 version identifiers indexed

## At a glance

- **Per-case verdicts, not just aggregates.** Every reported full-cohort run has 2,000 downloadable case records; each can be recounted against the published totals.
- **A complete version index.** Identifiers v1–v1660 are indexed with explicit gaps rather than silent omissions: 1,442 carry measurement records, 48 are fingerprint or mention only, and 170 have no located reference.
- **Content-free projections.** Admission recovery, retrieval partitions, fact coverage, and audit-feedback decisions are keyed to pseudonymous case identifiers, without enterprise text.

## Headline results

Same frozen 2,000 development cases for both arms.

| Arm | Strict | Partial | Strict + partial | End-to-end |
|---|---:|---:|---:|---:|
| Conventional RAG control | 1,318 (65.90%) | 422 | 1,740 (87.00%) | 1,103 (55.15%) |
| v1660, final tested configuration | 1,451 (72.55%) | 354 | 1,805 (90.25%) | 1,422 (71.10%) |

Strict counts correct answers and correct refusals; end-to-end pass applies the stored per-case product decision.
Both arms share the case set, generation and judge model names, reasoning effort, and offline judge contract.
The control uses dense-only retrieval with the v1660 candidate and context limits, without admission cleaning or online audit.
The comparison is between whole systems: it is not a layer ablation, and it is not a holdout evaluation.

## Full-cohort inventory

| Run | Cases | Strict | Partial | Strict + partial | End-to-end | Case records |
|---|---:|---:|---:|---:|---:|---|
| v1225 (deployed configuration) | 2,000 | 1,590 (79.50%) | 253 | 1,843 (92.15%) | 1,589 | [Download](evidence/version-recovery/v1225.jsonl.gz) |
| v1226 | 2,000 | 1,517 (75.85%) | 349 | 1,866 (93.30%) | 1,516 | [Download](evidence/version-recovery/v1226.jsonl.gz) |
| v1227 | 2,000 | 1,542 (77.10%) | 279 | 1,821 (91.05%) | 1,540 | [Download](evidence/version-recovery/v1227.jsonl.gz) |
| v1371 | 2,000 | 1,550 (77.50%) | 315 | 1,865 (93.25%) | 1,538 | [Download](evidence/version-recovery/v1371.jsonl.gz) |
| v1660 | 2,000 | 1,451 (72.55%) | 354 | 1,805 (90.25%) | 1,422 | [Proposed-system evaluation](evidence/proposed-system-evaluation/README.md) |

Judge protocols differ: v1225–v1371 were graded under protocol v5 and v1660 under v6.
Scores from different protocols are not directly comparable, and no cross-protocol causal reading is supported.
The full inventory, including intermediate and rejected runs, is in
[FULL_COHORT_EVALUATIONS.md](evidence/FULL_COHORT_EVALUATIONS.md).

## Recounting a run

Each case stream has one row per development case, with the recorded verdict and runtime decision:

- v1222, v1225, v1226, v1227, v1371 — `evidence/version-recovery/<version>.jsonl.gz`
- v1660 — [proposed-system evaluation](evidence/proposed-system-evaluation/README.md)
- Conventional RAG control — [baseline-system evaluation](evidence/baseline-system-evaluation/README.md)

Label definitions and denominator rules are in
[answer-quality reporting](docs/answer-quality-reporting.md).
Aggregate recounts can be reproduced with the commands below.

## Review entry points

| Document | What it gives |
|---|---|
| [Paginated evidence browser](evidence/review/README.md) | Actual result files and per-case verdicts, 50 versions per range |
| [Full-cohort inventory](evidence/FULL_COHORT_EVALUATIONS.md) | Every 2,000-case run, including intermediates and rejections |
| [Version index](evidence/ITERATION_HISTORY.md) | Complete identifier history, v1–v1660 |
| [Version recovery](evidence/version-recovery/README.md) | Recovered records and explicit gaps for all 1,660 identifiers |
| [Evaluation configurations](evidence/EVALUATION_CONFIGURATIONS.md) | Manuscript appendix: configuration families and archive index |
| [Audit-feedback supplement](evidence/audit-feedback/README.md) | Admission recovery, context repair, rollback, residual diagnostics |
| [Judge protocol](evidence/validation-protocols/semantic-judge-protocol.md) | Semantic-judge protocol and label definitions |
| [Export policy](evidence/validation-protocols/export-policy.md) | What is released, withheld, and why |
| [Architecture](docs/architecture.md) | System description |
| [Deployment and reproduction](docs/deployment-guide.md) | Runtime setup and regeneration |
| [Paper corrections](docs/paper-corrections.md) | Withdrawn or superseded interpretations |

## Version semantics

Three roles are kept apart. The **deployed configuration** is v1225, the configuration the enterprise runs. The **final tested checkpoint** is v1660. The **executed configuration** of a run is the version that produced its records. Some archived runs carry filing labels that differ from their configuration identifiers; this document uses configuration identifiers throughout. A version identifier may also name a comparator mentioned in a record or a document revision.
A mention does not establish a completed run.
The archive does not support a claim of 1,660 independent experiments, nor a component-level causal gain.

## Scope and limitations

- **One deployment.** The evidence comes from a single enterprise knowledge base; enterprise questions, answers, and source text are withheld.
- **One judge.** Offline scores come from a single recorded judge protocol (Sol v6 at v1660); independent human calibration was not performed.
- **Development cohort.** The evaluation cases also informed later revisions, so the scores characterize this cohort rather than held-out performance.
- **Whole-system contrast.** Indexing, ranking, online auditing, and decoding differ between arms; no layer is isolated.
- **Unmeasured costs.** Latency and serving cost were not measured.

## Reproduce aggregate checks

Python 3.10+ and the standard library are sufficient:

```bash
python3 tools/verify_evidence.py
python3 -m unittest discover -s tests
python3 framework/evaluation/recompute.py
```

With authorized access to the private experiment checkout:

```bash
python3 tools/export_evidence.py --source /path/to/private/repository
python3 tools/curate_evidence.py --source /path/to/private/repository
python3 tools/export_conventional_baseline.py --archive /path/to/private/control-archive
python3 -m pip install -r tools/requirements-export.txt
python3 tools/build_review_evidence.py --source /path/to/private/repository
python3 tools/recover_version_evidence.py --source /path/to/private/repository --backup /path/to/versioned/backups
python3 tools/index_version_references.py --source /path/to/private/repository --backup /path/to/versioned/backups
python3 tools/recover_embedded_results.py --source /path/to/private/repository --backup /path/to/versioned/backups
python3 tools/index_case_evaluations.py
python3 tools/finish_version_index.py
python3 tools/verify_evidence.py --write-manifest
```

The browser builder refuses to overwrite an existing `evidence/review` tree; archive it outside the repository before rebuilding.
The supplemental export checks private file hashes against the original inventory; changed or missing sources are reported, never silently substituted.
See the [browser repair report](docs/evidence-browser-repair.md) for scope and limitations.

The exporter reads private artifacts and never changes the source checkout.
It emits allowlisted statistics, pseudonymous case keys, and source hashes.
Repeating semantic grading or the original runtime requires the private corpus and infrastructure.

## Framework scope

The [PostgreSQL schema](framework/postgresql-staging/schema.sql),
[quality-gate example](framework/quality-gates/run_pipeline.py), and
[synthetic walkthrough](examples/quickstart.md) are teaching templates.
They are not the production implementation and do not recreate its scores.
Content judging is an explicit injected-verdict interface; missing verdicts remain pending review.

## Citing

```bibtex
@misc{wang2026reviewartifacts,
  author       = {Wang, Junjie and Zheng, Lihong},
  title        = {Dual-Layer Domain-Specific {RAG} with Audit Feedback: Evaluation Archive},
  year         = {2026},
  howpublished = {\url{https://github.com/sd4494093/hybrid-llm-domain-specific-rag}},
  note         = {Commit 6299e8ecc}
}
```

## License

See [LICENSE](LICENSE). Private enterprise source material is not distributed.
No additional content license, publication status, or automatic public-release schedule is asserted.
