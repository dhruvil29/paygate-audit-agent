"""Append-only JSONL audit trail with a SHA-256 hash chain.

Every record: timestamp (UTC, ISO-8601), action, inputs, decision,
approver, outcome, plus prev_hash / entry_hash. Tampering with any
earlier line breaks every later hash, which verify_trail() detects.

No secrets are ever written here: callers must pass redacted inputs
(see paypal_client.redact and cli, which strips credential-shaped keys).
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ZERO_HASH = "0" * 64


def _canonical(record: dict) -> str:
    return json.dumps(record, sort_keys=True, separators=(",", ":"))


def _hash(record: dict) -> str:
    return hashlib.sha256(_canonical(record).encode()).hexdigest()


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def last_hash(path: Path) -> str:
    if not path.exists():
        return ZERO_HASH
    prev = ZERO_HASH
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            prev = json.loads(line).get("entry_hash", prev)
    return prev


def append_entry(path: Path, *, action: str, inputs: dict, decision: str,
                 approver: str, outcome: str) -> dict:
    """Append one record; never rewrites history. Returns the record."""
    prev = last_hash(path)
    record = {
        "timestamp": _utcnow(),
        "action": action,
        "inputs": inputs,
        "decision": decision,
        "approver": approver,
        "outcome": outcome,
        "prev_hash": prev,
    }
    record["entry_hash"] = _hash(record)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(_canonical(record) + "\n")
    return record


def read_trail(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines()
            if line.strip()]


def verify_trail(path: Path) -> tuple[bool, str]:
    """Return (ok, message). Any broken link or bad hash fails."""
    prev = ZERO_HASH
    for i, record in enumerate(read_trail(path)):
        if record.get("prev_hash") != prev:
            return False, f"line {i + 1}: prev_hash link broken"
        entry_hash = record.pop("entry_hash", None)
        if _hash(record) != entry_hash:
            return False, f"line {i + 1}: entry_hash mismatch (tampered?)"
        prev = entry_hash
    return True, f"OK: {len(read_trail(path))} entries, chain intact"
