-- Synthetic teaching schema; not a migration of the private Dify database.
BEGIN;
CREATE SCHEMA IF NOT EXISTS staging;
CREATE TABLE IF NOT EXISTS staging.documents (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    source_key text NOT NULL UNIQUE,
    content_sha256 text NOT NULL CHECK (content_sha256 ~ '^[a-f0-9]{64}$'),
    status text NOT NULL DEFAULT 'extracted' CHECK (status IN (
        'extracted', 'rule_failed', 'rule_passed', 'ai_rejected',
        'needs_review', 'ai_passed', 'chunked', 'ingested', 'ingest_failed')),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS staging.quality_events (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    document_id bigint NOT NULL REFERENCES staging.documents(id),
    gate text NOT NULL CHECK (gate IN ('rule', 'ai', 'ingestion')),
    verdict text NOT NULL,
    policy_version text NOT NULL,
    evaluator_version text NOT NULL,
    content_sha256 text NOT NULL CHECK (content_sha256 ~ '^[a-f0-9]{64}$'),
    recorded_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS staging.chunks (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    document_id bigint NOT NULL REFERENCES staging.documents(id),
    position integer NOT NULL CHECK (position >= 1),
    content text NOT NULL,
    token_count integer NOT NULL CHECK (token_count BETWEEN 1 AND 800),
    tokenizer_version text NOT NULL,
    UNIQUE (document_id, position)
);
CREATE TABLE IF NOT EXISTS staging.ingestion_receipts (
    document_id bigint PRIMARY KEY REFERENCES staging.documents(id),
    dataset_key text NOT NULL,
    external_document_id text NOT NULL,
    completed_segments integer NOT NULL CHECK (completed_segments > 0),
    confirmed_at timestamptz NOT NULL,
    UNIQUE (dataset_key, external_document_id)
);
COMMIT;
