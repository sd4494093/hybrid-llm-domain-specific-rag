# Local Deployment and Review

## Offline Evidence Review

Python 3.10+ is sufficient for the exporter, curation, verifier and examples.
No third-party Python dependencies or API credentials are required. Run from
the repository root:

```bash
python3 tools/verify_evidence.py
python3 framework/evaluation/recompute.py
python3 -m unittest discover -s tests
```

For a specific version, open `evidence/iteration-milestones/v1660/README.md`.
Linked summary JSON files are readable directly on GitHub. The compressed
indexes retain full file, event and case projections for programmatic review.

## Synthetic PostgreSQL Example

Use a disposable PostgreSQL 14+ database with DDL privileges. The schema does
not require pgvector because embedding storage is outside this teaching example.
Set `DATABASE_URL` through your normal local credential mechanism, then:

```bash
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f framework/postgresql-staging/schema.sql
```

This creates only the example `staging` schema and tables. Do not point it at
an existing Dify database. Add application roles and permissions for an actual
deployment. Quality events should be append-only for application roles.

## Private-Side Rebuild

```bash
python3 tools/export_evidence.py --source /path/to/private/repository
python3 tools/curate_evidence.py --source /path/to/private/repository
python3 tools/verify_evidence.py --write-manifest
python3 tools/verify_evidence.py
```

Inventory hashing reads all files in the declared roots, including large
artifacts that remain hash-only. Ensure the source is quiescent. The scripts
record source changes and reject altered curated inputs. Regenerate in a clean
public output checkout when the source file set changes to avoid stale files.

This is an offline research artifact workflow. No live service, model endpoint,
database migration or publication is performed automatically.
