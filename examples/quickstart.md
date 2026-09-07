# Synthetic Gate Walkthrough

From the repository root, with Python 3.10+:

```bash
python3 framework/quality-gates/run_pipeline.py --input examples/documents.jsonl
python3 framework/evaluation/recompute.py
```

The first synthetic document passes structural checks but remains
`needs_review` because no AI verdict is supplied. The empty document returns
`rule_failed`. No API call occurs and no document is inserted in a database.

An optional verdict file is a JSON object keyed by input ID. Each verdict
must contain `content_sha256`, `policy_version`, `evaluator_version`, and
`verdict` (`pass`, `reject`, or `review`). Bind the hash to the exact UTF-8
document text. An absent or mismatched verdict cannot authorize ingestion.

These configurable thresholds are illustrative, not measured experimental
settings. Passing this example does not reproduce the private RAG system.
