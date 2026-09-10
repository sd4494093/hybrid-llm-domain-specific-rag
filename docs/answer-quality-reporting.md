# Answer Quality Reporting

The manuscript reports v1660 with three mutually exclusive categories:

| Category | Count / 2,000 | Rate |
|---|---:|---:|
| Strictly semantically correct | 1,451 | 72.55% |
| Partially correct: planner/prefill recovery | 411 | 20.55% |
| Remaining cases | 138 | 6.90% |
| Correct or partially correct (subtotal) | 1,862 | 93.10% |

The 411 planner/prefill recovery cases are partially correct and contribute to
usefulness. They do not contribute to strict semantic correctness. The remaining
138 cases partition into no-answer (108) and citation/source (30).

This reporting definition was clarified by the author on September 10, 2026.
The manuscript uses the terms **strict semantic correctness**, **partially
correct**, and **correct-or-partial usefulness**. Its headline metrics omit the
separate strict E2E metric, whose original results remain in the raw archive.

## Source Mapping

[Paper reporting](../evidence/v1660-final-baseline/paper-reporting.json) maps
the 1,451 strict successes and the 411 planner/partial ownership cases from the
[source summary](../evidence/v1660-final-baseline/summary.json). The original
Judge's five-label distribution remains available: 1,055 correct, 396 correct
refusal, 354 partial, 91 incorrect, and 104 incorrect refusal. The paper's
partially correct category is the recovery-layer grouping, not a rename of
the original 354-label count. The mapping preserves provenance and aggregate
accounting; it does not represent a new independent per-case semantic grading.

Do not add the 354 original partial labels to the 411 recovery cases. Do not
explain the remaining 138 as 58 + 104: those source/citation contract counts
sum to 162 and belong to a separate classification.

June MVP UAT remains 1,204 strictly correct and 587 partially correct, yielding
1,791/2,000 = 89.55% usefulness. Equal cohort sizes do not establish identical
questions, sources, evaluator models, or causal gate effects.
