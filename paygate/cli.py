"""PayGate Audit Agent CLI.

Usage (from the repo root, Python 3.11+, no pip installs needed):
  python -m paygate.cli audit --checkout examples/checkout-clean.json
  python -m paygate.cli audit-order --order-id MOCK-ORDER-OK
  python -m paygate.cli recover --order-id MOCK-ORDER-FAILED
  python -m paygate.cli trail --verify
  python -m paygate.cli demo --approve-demo   # scripted mock demo run

Money actions NEVER auto-run: `recover` prompts interactively, and
`demo` only proceeds on the explicit --approve-demo flag, which is
logged as approver "demo-operator (explicit --approve-demo flag)".
Default trail file: ./audit-trail.jsonl (override with --trail).
Default client: mock. Use --client real only with sandbox env vars.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .approval import ApprovalGate, recover_failed_payment
from .audit import Checkout, audit_checkout
from .audit_trail import append_entry, read_trail, verify_trail
from .paypal_client import build_client, redact
from .summarizer import deterministic_summary, llm_summary

DEFAULT_TRAIL = Path("audit-trail.jsonl")


def _mock_order_to_checkout(order: dict) -> Checkout:
    items = []
    for unit in order.get("purchase_units", []):
        for item in unit.get("items", []):
            amount = item.get("unit_amount", {})
            items.append({
                "name": item.get("name", ""),
                "quantity": int(item.get("quantity", 1)),
                "unit_price": amount.get("value", "0.00"),
                "currency": amount.get("currency_code", "USD"),
            })
    amount = order.get("purchase_units", [{}])[0].get("amount", {})
    return Checkout(items=items,
                    currency=amount.get("currency_code", "USD"),
                    total=amount.get("value"))


def _print_report(report) -> None:
    print(json.dumps(report.to_dict(), indent=2))
    print("\nSUMMARY (deterministic engine):")
    print(deterministic_summary(report))
    llm = llm_summary(report)
    if llm:
        print("\nSUMMARY (local LLM rewording):")
        print(llm)
    else:
        print("\nNote: LLM summarizer disabled — no local Ollama "
              "server reachable. Deterministic summary above is the "
              "complete output.")


def cmd_audit(args) -> int:
    data = json.loads(Path(args.checkout).read_text())
    report = audit_checkout(Checkout.from_dict(data))
    append_entry(args.trail, action="audit-checkout",
                 inputs=redact({"checkout_file": args.checkout,
                                "verdict": report.verdict}),
                 decision="n/a", approver="system",
                 outcome=f"verdict={report.verdict}")
    _print_report(report)
    return 0 if report.verdict != "BLOCK" else 2


def cmd_audit_order(args) -> int:
    client = build_client(args.client)
    order = client.get_order(args.order_id)
    print(f"Order source: {client.source} "
          f"(mock data is clearly labelled; never a real payment)")
    report = audit_checkout(_mock_order_to_checkout(order))
    append_entry(args.trail, action="audit-order",
                 inputs=redact({"order_id": args.order_id,
                                "source": client.source,
                                "status": order.get("status")}),
                 decision="n/a", approver="system",
                 outcome=f"verdict={report.verdict}")
    _print_report(report)
    return 0


def cmd_recover(args) -> int:
    client = build_client(args.client)
    gate = ApprovalGate(args.trail)
    result = recover_failed_payment(client, gate, args.order_id)
    print(json.dumps(result, indent=2))
    return 0 if result.get("outcome") in ("captured",
                                          "no-recovery-needed") else 1


def cmd_trail(args) -> int:
    if args.verify:
        ok, message = verify_trail(args.trail)
        print(message)
        return 0 if ok else 1
    for record in read_trail(args.trail):
        print(json.dumps(record))
    return 0


def cmd_demo(args) -> int:
    """Scripted end-to-end mock demo (used by DEMO.sh and the video)."""
    client = build_client("mock")
    trail = args.trail
    print("=== PayGate Audit Agent — scripted demo (MOCK data only) ===")
    print("Step 1: audit a clean checkout file.")
    report = audit_checkout(Checkout.from_dict(
        json.loads(Path("examples/checkout-clean.json").read_text())))
    append_entry(trail, action="audit-checkout",
                 inputs={"demo": True, "verdict": report.verdict},
                 decision="n/a", approver="system",
                 outcome=f"verdict={report.verdict}")
    print(deterministic_summary(report))
    print("\nStep 2: audit a flagged checkout file.")
    bad = audit_checkout(Checkout.from_dict(
        json.loads(Path("examples/checkout-flagged.json").read_text())))
    print(deterministic_summary(bad))
    print("\nStep 3: recovery flow for a FAILED mock order.")
    if not args.approve_demo:
        print("Recovery NOT attempted: re-run with --approve-demo to "
              "give the explicit demo approval (logged in the trail).")
        return 1
    gate = ApprovalGate(
        trail, approver="demo-operator (explicit --approve-demo flag)")
    result = recover_failed_payment(
        client, gate, "MOCK-ORDER-FAILED",
        decide=lambda action, details: "approve")
    print(json.dumps(result, indent=2))
    print("\nStep 4: verify the audit trail chain.")
    ok, message = verify_trail(trail)
    print(message)
    return 0 if ok else 1


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="paygate")
    parser.add_argument("--trail", type=Path, default=DEFAULT_TRAIL)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("audit")
    p.add_argument("--checkout", required=True)
    p = sub.add_parser("audit-order")
    p.add_argument("--order-id", required=True)
    p.add_argument("--client", default="mock", choices=["mock", "real"])
    p = sub.add_parser("recover")
    p.add_argument("--order-id", required=True)
    p.add_argument("--client", default="mock", choices=["mock", "real"])
    p = sub.add_parser("trail")
    p.add_argument("--verify", action="store_true")
    p = sub.add_parser("demo")
    p.add_argument("--approve-demo", action="store_true")
    args = parser.parse_args(argv)
    if args.command == "audit":
        return cmd_audit(args)
    if args.command == "audit-order":
        return cmd_audit_order(args)
    if args.command == "recover":
        return cmd_recover(args)
    if args.command == "trail":
        return cmd_trail(args)
    return cmd_demo(args)


if __name__ == "__main__":
    sys.exit(main())
