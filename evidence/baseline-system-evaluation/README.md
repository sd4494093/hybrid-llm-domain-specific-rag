# Baseline System Evaluation: Aggregated 2,000 Runs

The final combined machine-assisted evaluation reports 1,204 correct,
587 partial, 172 incorrect and 37 refusal labels. Exact recomputation gives
60.20% correctness and 89.55% correct-or-partial usefulness.

The initial Judge summary had 1,203 correct, 586 partial and two Judge errors.
The combined summary resolves those two errors: one additional correct and one
additional partial. This is why the initial and final counts differ.

## Published Evidence

- [Final summary](summary.json): aggregate metrics, source artifact ID and hash.
- [Initial summary](initial-summary.json): preserves the unresolved Judge stage.
- [Final per-run labels](case-labels.json): 2,000 pseudonymous records with
  labels and available answer/question hashes; no question or answer text.

Source contract: machine-assisted controller semantic evaluation. The observed
Judge model in the combined rows is `gpt-5.5`. An independent human gold
adjudication is not established by these files.

These are 2,000 aggregated runs, not a claim of 2,000 distinct prompts.
No regional table is published. This baseline evaluation does not share the
proposed system evaluation cohort hashes. Its refusal label cannot be equated
with the later correct-refusal contract.

The source summary rounds usefulness to 89.5%; the exact fraction
1,791/2,000 is 89.55%. Both the original projection and recomputed fraction
remain available. A causal quality-gate gain cannot be inferred merely by
subtracting this result from the proposed system evaluation.

See the [full iteration history](../ITERATION_HISTORY.md) and
[evaluation protocol](../validation-protocols/semantic-judge-protocol.md).
