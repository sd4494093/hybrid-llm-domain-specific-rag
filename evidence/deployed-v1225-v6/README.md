# Deployed v1225 versus conventional RAG

Both arms are evaluated on all 2,000 questions of the deployed run's revision-v4 development cohort, with the same v4 reference criteria and the same Sol/high v6 judge protocol. These are paired whole-system outcomes, not a layer ablation, a held-out test or a human calibration.

| Outcome | Conventional | v1225 | v1225 only | Control only | Net (percentage points) | Exact two-sided McNemar p |
|---|---:|---:|---:|---:|---:|---:|
| Strict | 1,316 | 1,521 | 359 | 154 | +205 (+10.25) | 6.77e-20 |
| Strict or partial | 1,741 | 1,856 | 202 | 87 | +115 (+5.75) | 1.07e-11 |
| End-to-end | 1,100 | 1,501 | 523 | 122 | +401 (+20.05) | 5.11e-60 |

Partial alone: 425 control, 335 v1225. Strict means correct answer or correct refusal. End-to-end is the recorded product-contract decision, not a synonym for strict correctness.

**What changed:** No v1225 answers were regenerated. Of its 2,000 original records, 1,979 had answers to regrade; 21 original runtime failures had no answer and remain uncertain, in the denominator. To align the conventional control to v4, 1,990 cases retained their original v6 verdicts, four retained their answers and context but were rejudged against the v4 reference, and six changed questions required fresh retrieval and generation under the frozen conventional configuration (Terra/high) followed by v6 judging. Both arms have determinate labels on these ten cases; none were imputed.

**Which comparison to cite:** The [historical v1225 result](../FULL_COHORT_EVALUATIONS.md) (1,590 strict, 1,589 end-to-end) used judge protocol v5. The [v1660 comparison](../baseline-system-evaluation/README.md) used revision-v19 questions and a different control total (1,318 strict, 1,103 end-to-end). Neither is the control for this table.

**Recount:** [Download the 2,000 pairs](pairs.csv) or run `python3 evidence/deployed-v1225-v6/recount.py` from the repository root (standard library only). Each row contains a release-specific case key, the control treatment, each arm's semantic label and its end-to-end flag (1 = pass). The file supports recounting the labels, not independently rejudging enterprise answers. No questions, answers, source URLs or judge rationales are released.
