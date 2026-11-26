# Evaluation Configurations and Archive Index

## Configuration families in the full-cohort comparisons

The planner runs are v1222, v1225, v1226, and v1227. The application requests 100 results. The manuscript's retrieval configuration section gives the internal search depths. The weighted ranker in v1371 uses the stored dense and lexical weights. The semantic ranker in v1660 does not use those weights.

| Setting | Planner runs | v1371 | v1660 |
| --- | --- | --- | --- |
| Question set | v4 | v19 | v19 |
| Application top-k | 100 | 100 | 100 |
| Stored dense/lexical | 0.50/0.50 | 0.65/0.35 | 0.65/0.35 |
| Ranking | BGE | Weighted | BGE |
| Reasoning effort | Medium | Low | High |
| Judge protocol | v5 | v5 | v6 |

The four planner runs share one runtime knowledge state. The two later runs share another, differing from the first by one active document and 95 segments within the same source inventory. The retained configurations do not identify the earlier serving models. In v1660, Terra serves answers and Sol judges them offline, both at high reasoning effort. [Archived run settings](audit-feedback/run-settings.json)

## Archive index

The index locates references for 1,490 of the 1,660 version identifiers. The remaining 170 have no located reference. A version mention alone does not establish a completed run. The retrieval comparisons use v241 through v243 for weights, v256 for the native BGE candidate, and v264 and v271 for cross-language retrieval and evidence selection. The v1371 full run is indexed under v1408. The integrated results use v1660 as their cutoff. [Version index](ITERATION_HISTORY.md) and [full-cohort evaluation inventory](FULL_COHORT_EVALUATIONS.md)

## Source-assisted lookup

A separate diagnostic on `dev_gold_2000.jsonl` used known source identities to construct URL-, title-, and summary-based queries against 8,747 documents and 199,136 segments. It stopped at the first variant that recovered the source in the top ten and recovered the source for all 2,000 cases. This result measures recoverability with source assistance. The manuscript evaluates question-only retrieval and answer quality separately.
