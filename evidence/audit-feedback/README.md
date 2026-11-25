# Audit-Feedback Supplement

This supplement binds the revised manuscript's selected feedback cases to
retained source files. It adds counts, pseudonymous joins, configuration values,
and decisions omitted by the earlier conservative export. It contains no
enterprise questions, answers, document text, source addresses, or credentials.
It is a static recount, not a new RAG experiment or a new semantic assessment.

| Material | What can be checked |
| --- | --- |
| [Admission and recovery](admission-recovery.json) | Five initial states; 115 rule clearances; 111 ingested, 2 rejected, 2 pending; document-set joins; 1,605 staging chunks |
| [Completed cycles](completed-cycles.json) | Context-continuity repair and local acceptance; later 200-case gate failure; rejected sibling-reranking candidate and actual revert commit |
| [Retrieval diagnosis](retrieval-diagnosis.json) | The 1,600-case partition into 564 source hits, 432 selection misses, and 604 candidate misses |
| [Fact coverage](fact-coverage.json) | Original 12-case fact counts; separate replay; 11 changed answers, so replay is not regrading |
| [Run settings](run-settings.json) | Six configurations' weights, reranking, reasoning effort, and runtime knowledge states |
| [Promotion decisions](promotion-decisions.json) | Strict-count promotion; 119 lost and 135 gained; later same-candidate self-comparison |
| [Ownership crosswalk](ownership-crosswalk.json) | Why the 411-case diagnostic bucket cannot substitute for 354 partial labels |
| [Input provenance](input-provenance.json) | Input fingerprints, existing inventory bindings where available, code-object hashes, and output fingerprints |

The context repair was accepted for local continuation after three controls and
a 17-case regression, not promoted as a population-level improvement. Its later
200-case evaluation failed the broader gate. The rejected reranking candidate
has a separate recorded code revert. By contrast, the final zero-delta decision
rechecks the already accepted candidate; it is not evidence that another
candidate was deployed and rolled back.

The 115 cleared rules represent 84.56% of the 136 original rule failures;
111 documents, or 81.62% of that original group, subsequently entered the index.
These operational outcomes do not provide independent human quality labels.
The later increase from 8,358 to 8,747 ingested documents exceeds this traced
recovery group by 278; no individual two-gate history is asserted for them.

Recount public joins and fingerprints with:

```bash
python3 tools/verify_audit_feedback.py
```

Re-exporting requires authorized access to the private source repository and
the explicit `--source` argument of `tools/export_audit_feedback.py`. The input
fingerprints establish which records were used, but cannot make confidential
source content independently readable. Complete final-cohort online verifier
intervention counts and an answer-audit-triggered rechunking example remain
unavailable. These limitations are retained in the manuscript.
