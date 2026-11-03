#!/bin/bash
# PayGate Audit Agent — scripted end-to-end demo (MOCK data only).
# No network calls, no real payments, no PayPal account needed.
# The recovery approval in this script is explicit: the --approve-demo
# flag, logged in the trail as approver
# "demo-operator (explicit --approve-demo flag)".
# Run from the repo root:  ./DEMO.sh
set -e
cd "$(dirname "$0")"
rm -f demo-trail.jsonl
echo "--- 1. Clean checkout audit (expect PASS) ---"
python3 -m paygate.cli --trail demo-trail.jsonl audit \
  --checkout examples/checkout-clean.json | head -30
echo ""
echo "--- 2. Flagged checkout audit (expect BLOCK, exit code 2) ---"
python3 -m paygate.cli --trail demo-trail.jsonl audit \
  --checkout examples/checkout-flagged.json | head -40 || true
echo ""
echo "--- 3. Full scripted demo: audit + flagged audit + gated recovery ---"
python3 -m paygate.cli --trail demo-trail.jsonl demo --approve-demo
echo ""
echo "--- 4. Audit trail (hash-chain verified above) ---"
python3 -m paygate.cli --trail demo-trail.jsonl trail | head -20
echo ""
echo "Demo complete. Trail file: demo-trail.jsonl"
