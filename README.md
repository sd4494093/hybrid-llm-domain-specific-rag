# Hybrid LLM Domain-Specific RAG: Review Artifacts

Companion artifacts for a research manuscript by Junjie Wang, Michael Bewong,
and Lihong Zheng. Publication acceptance is not claimed.

Start with the [iteration history](evidence/ITERATION_HISTORY.md) and the
[full-cohort evaluation inventory](evidence/FULL_COHORT_EVALUATIONS.md).
Every identifier from v1 to v1660 has a report, including identifiers for which
no reference was located. Version numbers do not establish experiment counts.

## Evidence Anchors

| Evaluation | Correctness contract | Result |
|---|---|---|
| Historical MVP UAT, 2,000 aggregated runs | Correct label | 1,204/2,000 = 60.20% |
| Historical MVP UAT | Correct plus partial | 1,791/2,000 = 89.55% |
| v1660, 2,000 natural-user cases | Correct plus correct refusal | 1,451/2,000 = 72.55% |
| v1660 | Strict E2E contract | 1,422/2,000 = 71.10% |

The cohorts and grading definitions differ. Equal sample sizes do not establish
a controlled comparison. The v1660 promotion decision records +16 semantic
successes over v1441, but the 85% target remains unmet. No v1660 usefulness
percentage is claimed.

## Review Entry Points

- [Complete version index](evidence/ITERATION_HISTORY.md)
- [Coverage and omissions](evidence/coverage.json)
- [Baseline evidence and retry resolution](evidence/baseline-UAT-20260608/README.md)
- [v1660 label and failure accounting](evidence/v1660-final-baseline/README.md)
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
python3 tools/verify_evidence.py --write-manifest
```

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
