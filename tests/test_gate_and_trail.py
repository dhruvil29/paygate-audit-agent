"""Tests: approval gate never auto-approves; trail chain detects tampering."""

import json

from paygate.approval import ApprovalGate, recover_failed_payment
from paygate.audit_trail import append_entry, verify_trail
from paygate.paypal_client import FakePayPalClient


def test_gate_logs_approval_and_rejection(tmp_path):
    trail = tmp_path / "trail.jsonl"
    gate = ApprovalGate(trail, approver="tester")
    assert gate.request("capture", {"order_id": "X"},
                        decide=lambda a, d: "approve") is True
    assert gate.request("capture", {"order_id": "X"},
                        decide=lambda a, d: "reject") is False
    # Anything that is not an exact "approve" is a rejection.
    assert gate.request("capture", {"order_id": "X"},
                        decide=lambda a, d: "yes") is False
    assert gate.request("capture", {"order_id": "X"},
                        decide=lambda a, d: "") is False
    assert verify_trail(trail)[0] is True
    assert len(trail.read_text().strip().splitlines()) == 4


def test_recovery_aborts_on_rejection(tmp_path):
    trail = tmp_path / "trail.jsonl"
    gate = ApprovalGate(trail, approver="tester")
    result = recover_failed_payment(
        FakePayPalClient(), gate, "MOCK-ORDER-FAILED",
        decide=lambda a, d: "reject")
    assert result["outcome"] == "aborted"
    assert verify_trail(trail)[0] is True


def test_recovery_of_failed_mock_order_reports_capture_failure(tmp_path):
    # The mock FAILED order cannot be captured; the flow must report
    # that honestly instead of pretending a retry succeeded.
    trail = tmp_path / "trail.jsonl"
    gate = ApprovalGate(trail, approver="tester")
    result = recover_failed_payment(
        FakePayPalClient(), gate, "MOCK-ORDER-FAILED",
        decide=lambda a, d: "approve")
    assert result["outcome"] == "capture-failed"
    assert verify_trail(trail)[0] is True


def test_recovery_not_needed_for_non_failed_order(tmp_path):
    trail = tmp_path / "trail.jsonl"
    gate = ApprovalGate(trail, approver="tester")
    result = recover_failed_payment(
        FakePayPalClient(), gate, "MOCK-ORDER-OK",
        decide=lambda a, d: "approve")
    assert result["outcome"] == "no-recovery-needed"


def test_tampered_trail_fails_verification(tmp_path):
    trail = tmp_path / "trail.jsonl"
    append_entry(trail, action="a", inputs={}, decision="n/a",
                 approver="t", outcome="ok")
    append_entry(trail, action="b", inputs={}, decision="n/a",
                 approver="t", outcome="ok")
    lines = trail.read_text().splitlines()
    record = json.loads(lines[0])
    record["outcome"] = "tampered"
    lines[0] = json.dumps(record)
    trail.write_text("\n".join(lines) + "\n")
    ok, message = verify_trail(trail)
    assert ok is False
    assert "tampered" in message or "mismatch" in message
