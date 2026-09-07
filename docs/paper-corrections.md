# Evidence-Driven Paper Corrections

This artifact update does not modify the Overleaf manuscript. Apply the
following corrections together before claiming an updated experimental result.

1. Replace the draft's unverified 75% proposed-system outcome with a clearly
   sourced experiment, or retain it only after locating its original per-case
   evidence. Current v1660 evidence supports 72.55% semantic correctness and
   71.10% strict E2E under the September natural-user contract.
2. Describe June MVP UAT as 2,000 aggregated runs. Its verified combined result
   is 1,204 correct and 587 partial. The earlier 1,203 count came from two
   unresolved Judge errors. The exact useful fraction is 89.55%.
3. Remove the claim that June and September share identical frozen questions,
   oracle hashes or evaluator models. Equal sample sizes alone do not provide
   a controlled comparison; refusal definitions also differ.
4. Use v1660's real label distribution: 1,055 correct, 396 correct_refusal,
   354 partial, 91 incorrect, 104 incorrect_refusal. Keep the 549 semantic
   failures, 578 E2E failures, and 411 planner/partial cohort distinct.
5. Withdraw 93.1% usefulness, zero refusal, and the 310/101 partial split.
   Correct refusal is desirable on negative cases; false refusal is a different
   metric. Avoid causal claims that all improvement results from ingestion gates.
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
