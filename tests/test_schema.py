"""Exercise the synthetic schema in an isolated local PostgreSQL instance."""

from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
PG_BIN = Path("/usr/lib/postgresql/18/bin")


@unittest.skipUnless((PG_BIN / "initdb").exists() and shutil.which("psql"), "PostgreSQL 18 server tools unavailable")
class SchemaTests(unittest.TestCase):
    def test_schema_and_chunk_bound(self):
        with tempfile.TemporaryDirectory(prefix="rag-schema-") as temporary:
            base = Path(temporary)
            cluster = base / "db"
            subprocess.run([str(PG_BIN / "initdb"), "-D", str(cluster), "-A", "trust", "--no-locale"], check=True, capture_output=True)
            subprocess.run([str(PG_BIN / "pg_ctl"), "-D", str(cluster), "-l", str(base / "server.log"),
                            "-o", f"-k {base} -p 55439 -c listen_addresses=''", "-w", "start"], check=True, capture_output=True)
            try:
                command = ["psql", "-h", str(base), "-p", "55439", "-d", "postgres", "-v", "ON_ERROR_STOP=1"]
                subprocess.run(command + ["-f", str(ROOT / "framework/postgresql-staging/schema.sql")], check=True, capture_output=True)
                sql = """
                INSERT INTO staging.documents (source_key, content_sha256)
                VALUES ('synthetic-test', repeat('a',64));
                INSERT INTO staging.chunks (document_id, position, content, token_count, tokenizer_version)
                VALUES (1, 1, 'synthetic text', 800, 'test-v1');
                """
                subprocess.run(command + ["-c", sql], check=True, capture_output=True)
                result = subprocess.run(command + ["-c", "INSERT INTO staging.chunks (document_id,position,content,token_count,tokenizer_version) VALUES (1,2,'too long',801,'test-v1')"], capture_output=True, text=True)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("check constraint", result.stderr)
            finally:
                subprocess.run([str(PG_BIN / "pg_ctl"), "-D", str(cluster), "-m", "fast", "-w", "stop"], check=True, capture_output=True)


if __name__ == "__main__":
    unittest.main()
