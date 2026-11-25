# Evidence-Driven Paper Corrections

Current reporting, November 25, 2026. Original proposed-system measurements and source hashes
remain unchanged. See [answer-quality reporting](answer-quality-reporting.md)
for the withdrawal of the previous ownership-based interpretation.

1. Replace the draft's unverified 75% proposed-system outcome with a clearly
   sourced experiment, or retain it only after locating its original per-case
   evidence. Report 72.55% strict semantic correctness and 90.25%
   correct-or-partial usefulness. Omit strict E2E from the manuscript's results;
   retain that original metric in the source evidence.
2. Report the [conventional RAG control](../evidence/baseline-system-evaluation/README.md)
   on the same 2,000 frozen cases as v1660, with the same answer and judge
   model names/effort and v1660 segment and context budgets: 1,318 strict and
   422 partial.
   All cases have Terra answers and Sol judgments after transport recovery.
3. Treat the contrast as whole-system evidence on development cases. It does
   not establish independent layer effects, identical source snapshots, or
   generalization to held-out cases.
4. Use original semantic labels: 1,451 strict, 354 partial, and 195 incorrect
   or incorrect-refusal outcomes. The 411 planner/context assignments are a
   diagnostic classification, not partial-answer labels.
5. Correct-or-partial correctness is (1,451 + 354)/2,000 = 90.25%. The previous
   93.10% interpretation is withdrawn. Its 138 remaining ownership assignments
   are not semantically incorrect outcomes. Preserve the 340 partial and 71
   incorrect labels within the 411 bucket, and the 14 partials outside it.
6. Label July's 100% Recall@10 as oracle-assisted lookup diagnostics. Runtime
   source acceptance@10 in v1660 is 1,483/1,600 (92.69%) and partly depends
   on answer citation judgments; exact-source hits are 784/1,600 (49%). Include
   denominators and do not call the former independent document recall.
7. Replace the obsolete statement that broad runtime evaluation could not run:
   v1660 completed 2,000 cases with 48 retry recoveries. Provider instability
   remains a measured limitation, not the absence of a broad result.
8. Version ingestion statistics. The 8,358/190,555 and 8,747/199,136 snapshots
   belong to earlier ingestion records; do not silently relabel them as a
   September measurement. Staging inventory and ingested document counts are
   different quantities. The five initial admission states are 8,358 ingested,
   136 rule failed, 957 model rejected, 375 pending review, and 335 processing
   failures. The 1,803 non-ingested documents are not all quality rejections.
9. Replace an invented monotonic 1,660-step chart with the indexed evidence
   history. Include failed, aborted and unproven candidates. Version numbers
   do not establish 1,660 experiments or successful improvements.
10. Rebuild quality figures from the matching source summary. A heatmap of
    language/domain or a version transition table is useful only with explicit
    denominators and compatible metrics. Retain no duplicate Answer Count plot
    and no regional comparison table.

The [audit-feedback supplement](../evidence/audit-feedback/README.md) traces
115 selected rule retests through 111 successful ingestions, a locally accepted
context repair, and a rejected and reverted candidate. The late full-cohort
promotion requires a numerical strict-count increase; +16 is not a significance
criterion. A later self-comparison is not independent rollback evidence.

The public archive records missing references and withheld private content.
It supports aggregate verification, not an unqualified full reproducibility
claim. Multiple uses of a development cohort and Judge variation must be
discussed in limitations; no held-out evaluation is established here.
