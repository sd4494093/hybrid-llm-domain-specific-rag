# v1660-Parameter-Aligned Conventional RAG Control: 2,000 Cases

The control used the same v19 development cases, answer and judge model names,
reasoning effort, and Sol v6 protocol as v1660. It applied the pinned v1660
800-character, zero-overlap native segmenter to raw extracted text without
admission filtering or cleaning. Dense-only cosine search retrieved up to 100
candidates. A frozen v1660 question-only rule selected at most five parents and
10 segments normally or 16 for broad queries; these segments alone were sent to
GPT-5.6-Terra/high. The 100 candidates are retained for retrieval traceability,
not passed to the answer model. No online audit or iterative repair was used.
GPT-5.6-Sol/high scored all answers offline under the v6 contract.

| Metric | Conventional RAG | Archived v1660 |
|---|---:|---:|
| Strict correctness, including correct refusals | 1,318/2,000 (65.90%) | 1,451/2,000 (72.55%) |
| Strict or partial correctness | 1,740/2,000 (87.00%) | 1,805/2,000 (90.25%) |
| Exact expected-source hits in first 10 prompt-visible segments | 824/1,600 (51.50%) | 784/1,600 (49.00%) |
| Product-contract end-to-end pass | 1,103/2,000 (55.15%) | 1,422/2,000 (71.10%) |

The control answered 1,996 cases on the first attempt and recovered four
transport failures by replaying the original requests on the configured
secondary provider lane. All 2,000 answers were graded with no final judge
errors or skips. The end-to-end contract combines citation, response format,
and semantic requirements; it is not a pure semantic capability measure.

Paired strict outcomes changed in 339 cases from not strict in the control to
strict in v1660, and in 206 cases in the opposite direction (net +133).
Strict-or-partial outcomes changed 186/121 in those respective directions.
Exact expected-source hits are somewhat higher in the dense-only control; this
does not establish greater retrieval quality or explain answer scores. The
E2E contract combines response-format, citation, and semantic requirements;
it is not a pure semantic capability measure.

This is a shared-cohort whole-system comparison, not a layer ablation or holdout
evaluation. The extracted raw corpus is not attested byte-identical to the
historical v1660 corpus, and the historical provider weight snapshots are
unavailable. Model names and reasoning effort are matched.

- [Recomputable metrics, paired transitions, and fingerprints](summary.json)
- [All 2,000 pseudonymous labels and outcome flags](case-labels.json)
- [Archived v1660 evidence](../proposed-system-evaluation/README.md)

Case keys join the two arms without exposing question or answer text, retrieved
excerpts, internal URLs, or credentials. The public records support aggregate
replication, not independent semantic regrading.
