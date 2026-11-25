#!/usr/bin/env python3
"""Offline gate contract example. No provider calls or database mutations."""

import argparse
import hashlib
import json
from pathlib import Path


def evaluate(text, policy, verdict=None):
    content_hash = hashlib.sha256(text.encode()).hexdigest()
    result = {"content_sha256": content_hash, "policy_version": policy["policy_version"]}
    length = len(text.strip())
    if length < policy["min_characters"] or length > policy["max_characters"]:
        return dict(result, status="rule_failed", reason="length_outside_policy")
    if text.count("\ufffd") / max(1, len(text)) > policy["max_replacement_fraction"]:
        return dict(result, status="rule_failed", reason="encoding_replacement_ratio")
    if verdict is None:
        return dict(result, status="needs_review", reason="ai_verdict_missing")
    required = {"content_sha256", "policy_version", "evaluator_version", "verdict"}
    if not required <= verdict.keys() or verdict["content_sha256"] != content_hash or verdict["policy_version"] != policy["policy_version"]:
        return dict(result, status="needs_review", reason="verdict_binding_invalid")
    if not isinstance(verdict["evaluator_version"], str) or not verdict["evaluator_version"].strip():
        return dict(result, status="needs_review", reason="evaluator_version_missing")
    statuses = {"pass": "ai_passed", "reject": "ai_rejected", "review": "needs_review"}
    return dict(result, status=statuses.get(verdict["verdict"], "needs_review"), reason="recorded_ai_verdict")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True, help="JSONL with synthetic id and text")
    parser.add_argument("--verdicts", type=Path, help="Optional JSON object indexed by document id")
    parser.add_argument("--config", type=Path, default=Path(__file__).with_name("config.json"))
    args = parser.parse_args()
    policy = json.loads(args.config.read_text())
    assert 0 <= policy["min_characters"] <= policy["max_characters"]
    assert 0 <= policy["max_replacement_fraction"] <= 1
    verdicts = json.loads(args.verdicts.read_text()) if args.verdicts else {}
    seen = set()
    with args.input.open() as stream:
        for line in stream:
            if not line.strip():
                continue
            row = json.loads(line)
            if row["id"] in seen:
                raise ValueError("Duplicate document id")
            seen.add(row["id"])
            print(json.dumps({"id": row["id"], **evaluate(row["text"], policy, verdicts.get(row["id"]))}))


if __name__ == "__main__":
    main()
