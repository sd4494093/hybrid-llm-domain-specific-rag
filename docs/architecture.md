# Framework and Evidence Architecture

This release separates a read-only evidence exporter from a synthetic ingestion
contract example. Neither component connects to the private live Dify system.

The evidence pipeline inventories files, hashes them, projects whitelisted
statistics, indexes version references, recomputes selected final labels and
verifies public outputs. The raw corpus and runtime answers stay private.

The ingestion example models extraction records, a deterministic structural
gate, a content-bound AI verdict, bounded chunks and external ingestion
receipts. Quality events retain the policy/evaluator/content versions needed
to audit decisions. The application should write state and event changes in a
single short transaction; provider work happens outside that transaction.

Staging includes rejected and pending documents. Its total must not be equated
with vector database document count. Reconciliation compares completed
ingestion receipts with active external documents, including segment counts
and source identity. Count equality alone does not establish identity equality.

## Extension Boundaries

An actual deployment needs extraction, tokenization with the embedding model's
tokenizer, embedding generation, Dify integration, credential management,
retry handling and source metadata. The example schema's 800-token constraint
checks a reported count; it does not tokenize content automatically.

Hybrid retrieval and context planning in the evaluated private implementation
are not copied into a generic template and are not reproduced by this example.
The public archive records observable outputs and contracts, not a claim of
deployable production parity.
