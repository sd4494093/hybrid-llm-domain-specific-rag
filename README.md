# Dual-Layer Domain-Specific RAG with Audit Feedback: Review Artifacts

Companion artifacts for a research manuscript by Junjie Wang, Michael Bewong,
and Lihong Zheng. Publication acceptance is not claimed.

Start with the [paginated evidence browser](evidence/review/README.md), the
[iteration history](evidence/ITERATION_HISTORY.md) and the
[full-cohort evaluation inventory](evidence/FULL_COHORT_EVALUATIONS.md).
Every identifier from v1 to v1660 has a report, including identifiers for which
no reference was located. Version numbers do not establish experiment counts.

## Evidence Anchors

| Evaluation | Correctness contract | Result |
|---|---|---|
| Conventional RAG control, same 2,000 development cases | Correct plus correct refusal | 1,318/2,000 = 65.90% |
| Conventional RAG control | Correct or partially correct | 1,740/2,000 = 87.00% |
| Conventional RAG control, grounded cases | Exact expected-source hit in first 10 prompt-visible segments | 824/1,600 = 51.50% |
| Conventional RAG control | End-to-end pass under product contract | 1,103/2,000 = 55.15% |
| Proposed system, 2,000 enterprise development cases | Correct plus correct refusal | 1,451/2,000 = 72.55% |
| Proposed system | Original semantic partial label | 354/2,000 = 17.70% |
| Proposed system | Correct or partially correct | 1,805/2,000 = 90.25% |

Both arms use the same frozen development cases, generation/judge model names,
reasoning effort, and offline judge contract. The control uses the v1660
candidate and context limits but dense-only retrieval with no admission
cleaning, answer audit, or iterative revision. The comparison is between whole
systems, not a layer ablation or a holdout evaluation.
The proposed system evaluation records +16 semantic
successes over an earlier iteration (v1441), but the 85% strict semantic target remains unmet.
See the [answer-quality reporting definition](docs/answer-quality-reporting.md)
for the label-based calculation and withdrawal of the previous ownership-based
93.10% interpretation. The 411 planner/context investigation assignments are
not partial labels. Original machine labels and strict E2E results remain unchanged.

The [audit-feedback supplement](evidence/audit-feedback/README.md) links
admission recovery, local context repair, candidate rollback, configuration
families, and residual diagnostics to content-free source projections. These
records support the dual-layer architecture, not a claim of 1,660 independent
experiments or a component-level causal gain.

## Review Entry Points

- [Actual result files and per-case verdicts, 50 versions per range](evidence/review/README.md)
- [Supplemental coverage and remaining gaps](evidence/review/coverage.json)
- [Complete version index](evidence/ITERATION_HISTORY.md)
- [Recovered records and explicit gaps for all 1,660 identifiers](evidence/version-recovery/README.md)
- [Manuscript appendix: evaluation configurations and archive index](evidence/EVALUATION_CONFIGURATIONS.md)
- [Coverage and omissions](evidence/coverage.json)
- [v1660-parameter-aligned conventional RAG control: all 2,000 cases](evidence/baseline-system-evaluation/README.md)
- [Proposed system label and failure accounting](evidence/proposed-system-evaluation/README.md)
- [Evaluation protocol](evidence/validation-protocols/semantic-judge-protocol.md)
- [Export policy](evidence/validation-protocols/export-policy.md)
- [Architecture](docs/architecture.md)
- [Deployment and reproduction](docs/deployment-guide.md)
- [Paper corrections](docs/paper-corrections.md)

## Reproduce Aggregate Checks

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

The browser builder refuses to overwrite an existing `evidence/review` tree.
Archive it outside the repository before rebuilding. The supplemental export
checks private file hashes against the original inventory; changed or missing
sources are reported, never silently substituted. See the
[browser repair report](docs/evidence-browser-repair.md) for scope and limitations.

The exporter reads private artifacts; it never changes the source checkout.
It emits allowlisted statistics, pseudonymous case keys, and source hashes.
The archive supports accounting and provenance review. Repeating semantic
grading or the original runtime requires the private corpus and infrastructure.

## Framework Scope

The [PostgreSQL schema](framework/postgresql-staging/schema.sql),
[quality-gate example](framework/quality-gates/run_pipeline.py), and
[synthetic walkthrough](examples/quickstart.md) are newly written teaching
templates. They are not the production Dify implementation and do not recreate
its scores. Content judging is an explicit injected verdict interface;
missing verdicts remain pending review.

## License

See [LICENSE](LICENSE). Private enterprise source material is not distributed.
No additional content license, publication status, or automatic public-release
schedule is asserted.
