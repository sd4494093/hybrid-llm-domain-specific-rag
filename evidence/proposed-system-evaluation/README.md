# Proposed System Evaluation: Natural-User Cases

Evidence finalized September 7, 2026. The full cohort contains 2,000 cases:
1,600 grounded-answer cases, 300 no-answer cases and 100 policy-refusal cases.
The answer model is recorded as `gpt-5.6-terra/high`; the separate Judge uses
`gpt-5.6-sol/high`. Model names are experiment configuration identifiers.

## Paper Results

The paper reports 1,451 strictly semantically correct cases (72.55%), 411
partially correct planner/prefill recovery cases (20.55%), and 138 remaining
cases (6.90%). Correct-or-partial usefulness is 1,862/2,000 = 93.10%.
See [paper reporting](paper-reporting.json) and the
[definition and source mapping](../../docs/answer-quality-reporting.md).

## Original Automated Judge Labels

| Judge label | Count |
|---|---:|
| correct | 1,055 |
| correct_refusal | 396 |
| partial | 354 |
| incorrect | 91 |
| incorrect_refusal | 104 |
| Total | 2,000 |

Semantic correctness counts correct plus correct_refusal:
1,451/2,000 = 72.55%. Partial is not a semantic success under this gate.
Strict E2E success adds source and refusal contracts: 1,422/2,000 = 71.10%.
The semantic target is 1,700/2,000 = 85%, leaving 249 cases to recover.

## Distinct Failure Contracts

Semantic failures total 549. The independent owning-layer cohort partitions
them into planner/partial 411, no-answer 108, and citation/source 30.
The 411 bucket is classified as partially correct for the paper's usefulness
measure. It is distinct from the original Judge's partial count (354).

Strict E2E failures total 578: citation_wrong_source 58, grounded_no_answer 104,
semantic_judge_rejected 382, no_answer_incorrect 3, semantic_incomplete 10,
and semantic_incorrect 21. These categories must not be added to the
semantic labels or owning-layer buckets.

## Retrieval and Reliability

Reported runtime source Recall@10 is 1,483/1,600 = 92.6875%, using the grounded
subset and the evaluator's source contract. It is distinct from an earlier
oracle-assisted document lookup diagnostic, which reached 100% over a
different 2,000-case set using source identity query variants.

Final runtime coverage is 2,000/2,000: 1,952 first-attempt successes and 48
recoveries. The original full batch retained four transport failures after
in-run retries; an additional bounded resume recovered those four. Thus
100% coverage is retry-inclusive, not a zero-error first attempt.
Final Judge error and uncertain counts are both zero, following one uncertain
judgment resolution in the final Judge merge.

## Acceptance and Limits

The internal promotion decision compares an earlier iteration's 1,435 semantic successes with the proposed system's
1,451, a net gain of 16 (+0.80 percentage points). Promotion establishes the
next local iteration baseline; it does not establish production readiness,
the 85% target, per-case monotonicity, or statistical significance.
The baseline system evaluation uses a different question and grading contract.

The paper's 93.1% usefulness includes 411 partially correct recovery cases.
The remaining 138 partition into no-answer 108 and citation/source 30.
Zero refusal, the unsupported 310/101 split, and invented early milestones
are not claimed. Corpus and filtering statistics from earlier ingestion
snapshots are not asserted as proposed system runtime measurements.

## Files

- [Recomputed summary](summary.json)
- [Projected final evaluation](evaluation.json)
- [Projected Judge merge](judge.json)
- [Projected promotion decision](promotion.json)
- [Projected failure cohort](failure-cohort.json)
- [All 2,000 Judge labels](case-labels.json)
- [All 2,000 E2E judgments](case-evaluation.json)
- [v1660 path-associated artifacts](../iteration-milestones/v1660/README.md)

Source SHA-256 and artifact IDs bind each projection to the private record.
The release excludes enterprise text, original URLs and credentials. It
supports aggregate replication, not independent content grading without
access to the private sources.
