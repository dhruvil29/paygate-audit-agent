"""Human approval gate: NOTHING touching money proceeds without it.

Rules, enforced in code, not just docs:
  1. Every money action (create order, capture, retry) calls
     request_approval() first and proceeds ONLY on an explicit
     "approve" decision.
  2. There is no --yes / auto-approve flag for money actions anywhere
     in the CLI. The only non-interactive path is a decision function
     supplied by the caller (tests, or the demo command with its
     explicit --approve-demo flag, which is itself logged as the
     approver). Silence, EOF, and anything other than an exact
     "approve" counts as rejection.
  3. Every decision is written to the audit trail, approve or reject.
"""

from __future__ import annotations

from pathlib import Path

from . import audit_trail


class ApprovalGate:
    def __init__(self, trail_path: Path, approver: str = "operator"):
        self.trail_path = Path(trail_path)
        self.approver = approver

    def request(self, action: str, details: dict,
                decide=None) -> bool:
        """Return True only on an explicit approve. Always logs."""
        if decide is not None:
            decision = decide(action, details)
        else:
            print(f"\nAPPROVAL REQUIRED: {action}")
            for key, value in details.items():
                print(f"  {key}: {value}")
            answer = input("Type 'approve' to proceed, anything else "
                           "to reject: ").strip().lower()
            decision = "approve" if answer == "approve" else "reject"
        approved = (decision == "approve")
        audit_trail.append_entry(
            self.trail_path, action=f"approval:{action}",
            inputs=details, decision=decision, approver=self.approver,
            outcome="approved" if approved else "rejected")
        return approved


def recover_failed_payment(client, gate: ApprovalGate, order_id: str,
                           decide=None) -> dict:
    """Recovery flow for a failed payment.

    Steps, each gated separately: (1) re-check the order, (2) propose a
    retry capture, (3) only on approval, attempt the capture. A
    rejection at any step aborts the flow and is logged; nothing
    retries automatically and nothing retries in a loop.
    """
    order = client.get_order(order_id)
    if order.get("status") != "FAILED":
        return {"order_id": order_id, "status": order.get("status"),
                "outcome": "no-recovery-needed",
                "note": "Order is not FAILED; recovery not attempted."}
    if not gate.request("recheck-failed-order",
                        {"order_id": order_id,
                         "failure_reason": order.get("failure_reason", "")},
                        decide=decide):
        return {"order_id": order_id, "outcome": "aborted",
                "step": "recheck-failed-order"}
    if not gate.request("retry-capture",
                        {"order_id": order_id,
                         "amount": order.get("purchase_units", [{}])[0]
                         .get("amount", {})},
                        decide=decide):
        return {"order_id": order_id, "outcome": "aborted",
                "step": "retry-capture"}
    try:
        result = client.capture_order(order_id)
        outcome = "captured" if result.get("status") == "COMPLETED" \
            else f"capture-returned-{result.get('status')}"
    except Exception as exc:  # mock FAILED capture, real API errors
        audit_trail.append_entry(
            gate.trail_path, action="retry-capture-attempt",
            inputs={"order_id": order_id}, decision="approved",
            approver=gate.approver, outcome=f"failed: {exc}")
        return {"order_id": order_id, "outcome": "capture-failed",
                "error": str(exc)}
    audit_trail.append_entry(
        gate.trail_path, action="retry-capture-attempt",
        inputs={"order_id": order_id}, decision="approved",
        approver=gate.approver, outcome=outcome)
    return {"order_id": order_id, "outcome": outcome,
            "capture": result}
