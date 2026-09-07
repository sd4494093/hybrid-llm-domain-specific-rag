# Evaluation Contracts

## Historical MVP UAT

Report a single aggregate of 2,000 runs. The combined machine-assisted Judge
labels are correct, partial, incorrect and refusal. Strict correctness counts
only correct; usefulness counts correct plus partial. Preserve the two initial
Judge failures and their resolved combined artifact. Do not attach September
question/oracle hashes or Judge model names to the June run.

## Natural-User Dev Evaluation

Freeze questions, expected facts, approved source evidence, refusal policy,
cohort order and source snapshot. Store hashes and code/model configuration.
The v1660 cohort is 1,600 grounded, 300 no-answer and 100 policy-refusal cases.
The runtime input is question-only. Oracle answers, expected document IDs,
titles, URLs and evaluator hints must not be injected into runtime questions.
Record the original response before grading.

Use a separate semantic Judge bound to the exact question, response and source
evidence. Here the recorded serving model is `gpt-5.6-terra/high`, while the
Judge is `gpt-5.6-sol/high`. These are reported provider identifiers, not an
independently verified statement of backend model provenance.

Semantic correctness is `(correct + correct_refusal) / 2000`. Partial labels
fail this contract. Strict E2E success additionally requires the evaluator's
source/citation and no-answer/refusal checks. Report these two outcomes
separately. Retrieval Recall@10 and citation support use 1,600 grounded cases
as denominator; correct refusal uses the 400 refusal/no-answer cases.

Retries preserve originals, attempt history and identity-bound replacements.
Transport success after retries is distinct from first-attempt success. Do not
retry deterministic semantic failures until they pass. A resolved uncertain
Judge result must retain its initial state and replacement lineage.

## Comparing Iterations

Join cases only within compatible question, oracle, source and evaluator
contracts. Compare code/model configuration separately; equal hashes of the
question set alone do not establish identical experimental conditions.
Disclose regressions and no-go outcomes as well as improvements. Full results,
subsets, smoke tests and interrupted runs are separate evidence populations.
Never sum their rows or select their maximum score as a final result.

The v1660 baseline decision uses a strict numerical improvement over v1441;
its +16 count is not a statistical significance test. The same cohort has
been used repeatedly for development, so treat it as a development benchmark.
A held-out evaluation and Judge repeatability analysis are required for
unbiased generalization claims. The 85% semantic target is still unmet.

## Historical Lookup Diagnostic

The July 2,000-case source-identity retrieval test tried URL/title/summary
query variants and scored the first successful candidate against an expected
document ID. Its 100% Recall@10 is oracle-assisted document recovery. It does
not estimate ordinary-user runtime accuracy or the later question-only recall.

## Reproduction Boundary

The public projections reproduce counts and joins. They omit enterprise text
and cannot reproduce semantic judgments or Dify runtime independently. The
synthetic framework examples demonstrate contracts without claiming to be
the tested production implementation.
