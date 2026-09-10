# Evidence-Driven Paper Corrections

The manuscript and evidence use the following reporting definitions. See
[answer-quality reporting](answer-quality-reporting.md) for the partial-recovery
classification clarified on September 10, 2026.

1. Replace the draft's unverified 75% proposed-system outcome with a clearly
   sourced experiment, or retain it only after locating its original per-case
   evidence. Report 72.55% strict semantic correctness and 93.1%
   correct-or-partial usefulness. Omit strict E2E from the manuscript's results;
   retain that original metric in the source evidence.
2. Describe June MVP UAT as 2,000 aggregated runs. Its verified combined result
   is 1,204 correct and 587 partial. The earlier 1,203 count came from two
   unresolved Judge errors. The exact useful fraction is 89.55%.
3. Remove the claim that June and September share identical frozen questions,
   oracle hashes or evaluator models. Equal sample sizes alone do not provide
   a controlled comparison; refusal definitions also differ.
4. Use the paper grouping: 1,451 strictly semantically correct, 411 partially
   correct planner/prefill recovery cases, and 138 remaining cases. Preserve
   original automated Judge labels in the archive, including 354 original
   partial labels. Explain the recovery-layer mapping in the evaluation method.
5. Correct-or-partial usefulness is (1,451 + 411)/2,000 = 93.1%. The remaining
   138 are no-answer 108 plus citation/source 30, not 58 + 104. Do not invent
   a 310/101 split or claim zero refusal. Do not attribute all improvements
   causally to ingestion gates.
6. Label July's 100% Recall@10 as oracle-assisted lookup diagnostics. Runtime
   source Recall@10 in v1660 is 1,483/1,600 (92.6875%). Include the denominator
   and source contract in table captions.
7. Replace the obsolete statement that broad runtime evaluation could not run:
   v1660 completed 2,000 cases with 48 retry recoveries. Provider instability
   remains a measured limitation, not the absence of a broad result.
8. Version ingestion statistics. The 8,358/190,555 and 8,747/199,136 snapshots
   belong to earlier ingestion records; do not silently relabel them as a
   September measurement. Staging inventory and ingested document counts are
   different quantities. Historical cost estimates need their own evidence.
9. Replace an invented monotonic 1,660-step chart with the indexed evidence
   history. Include failed, aborted and unproven candidates. Version numbers
   do not establish 1,660 experiments or successful improvements.
10. Rebuild quality figures from the matching source summary. A heatmap of
    language/domain or a version transition table is useful only with explicit
    denominators and compatible metrics. Retain no duplicate Answer Count plot
    and no regional comparison table.

The public archive records missing references and withheld private content.
It supports aggregate verification, not an unqualified full reproducibility
claim. Multiple uses of a development cohort and Judge variation must be
discussed in limitations; no held-out evaluation is established here.
