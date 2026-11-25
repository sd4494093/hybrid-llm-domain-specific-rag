# Answer Quality Reporting

Current manuscript definition, corrected November 17, 2026. No new semantic
grading was performed. The original automated labels are the reporting basis.

| Semantic outcome | Count / 2,000 | Rate |
|---|---:|---:|
| Strict: correct plus correct refusal | 1,451 | 72.55% |
| Partial label | 354 | 17.70% |
| Incorrect or incorrect refusal | 195 | 9.75% |
| Strict plus partial (subtotal) | 1,805 | 90.25% |

The five original labels are 1,055 correct, 396 correct refusal, 354 partial,
91 incorrect, and 104 incorrect refusal. The strict numerator includes correct
refusals; the answerable-only strict result is 1,055/1,600 = 65.94%.

## Diagnostic Ownership Is a Different Classification

The 549 non-strict cases have diagnostic assignments: planner/partial 411,
no-answer 108, and citation/source 30. These describe where to investigate,
not new semantic verdicts. The 411 include 340 partial and 71 incorrect labels;
14 original partial cases lie outside that bucket. Adding 411 to 1,451 would
therefore replace a label classification with a diagnostic one.

The September 10 interpretation, 1,862/2,000 = 93.10%, is withdrawn as a
correct-or-partial answer rate. Its 138 remaining ownership assignments are
not the 195 semantically incorrect outcomes. Raw labels, original diagnostic
assignments, dates, and source fingerprints remain unchanged. Git history
retains the superseded document; the current machine-readable record explicitly
records its withdrawal instead of rewriting the original experiment.

## Reproduction and Comparison

[Paper reporting](../evidence/proposed-system-evaluation/paper-reporting.json)
is checked against [all case labels](../evidence/proposed-system-evaluation/case-labels.json)
by `framework/evaluation/recompute.py`. A source-bound, pseudonymous
[ownership crosswalk](../evidence/audit-feedback/ownership-crosswalk.json)
supports the 340/71/14 overlap calculation without exposing enterprise text.

The [v1660-parameter-aligned conventional RAG control](../evidence/baseline-system-evaluation/README.md)
scored 1,318 strict and 422 partial outcomes on the same 2,000 development
cases and under the same judge contract. This is a whole-system comparison,
not a layer ablation or holdout evaluation.
