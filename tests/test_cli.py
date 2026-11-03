"""End-to-end CLI tests (mock path only; no network)."""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run_cli(*args, cwd, trail=None):
    # --trail is a global option: it must precede the subcommand.
    prefix = ["--trail", str(trail)] if trail is not None else []
    return subprocess.run(
        [sys.executable, "-m", "paygate.cli", *prefix, *args],
        cwd=cwd, capture_output=True, text=True, timeout=60)


def test_cli_audit_clean_and_flagged(tmp_path):
    clean = run_cli("audit", "--checkout",
                    "examples/checkout-clean.json",
                    cwd=ROOT, trail=tmp_path / "t.jsonl")
    assert clean.returncode == 0, clean.stdout + clean.stderr
    assert "PASS" in clean.stdout
    flagged = run_cli("audit", "--checkout",
                      "examples/checkout-flagged.json",
                      cwd=ROOT, trail=tmp_path / "t.jsonl")
    assert flagged.returncode == 2  # BLOCK exit code
    assert "BLOCK" in flagged.stdout
    assert "CURRENCY_MISMATCH" in flagged.stdout


def test_cli_demo_and_trail_verify(tmp_path):
    trail = tmp_path / "t.jsonl"
    demo = run_cli("demo", "--approve-demo", cwd=ROOT, trail=trail)
    assert demo.returncode == 0, demo.stdout + demo.stderr
    assert "chain intact" in demo.stdout
    verify = run_cli("trail", "--verify", cwd=ROOT, trail=trail)
    assert verify.returncode == 0
    assert "chain intact" in verify.stdout


def test_cli_demo_without_approval_does_not_recover(tmp_path):
    demo = run_cli("demo", cwd=ROOT, trail=tmp_path / "t.jsonl")
    assert demo.returncode == 1
    assert "NOT attempted" in demo.stdout
