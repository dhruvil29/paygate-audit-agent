# YouTube upload package — PayGate Audit Agent (PREPARED, NOT UPLOADED)

Video file: `demo/demo-video.mp4` (48s, 1280x720, h264, decode-verified
2026-10-29). Rendered from real CLI output of the mock-data demo.
Upload is a human-only step — no upload has been made by this build.

## Title

PayGate Audit Agent — audit before you pay, never retry without a human

## Description

PayGate Audit Agent audits a checkout BEFORE payment: it itemizes every
fee, recomputes the total from the line items, summarizes the terms, and
flags anomalies (currency mismatch, unusual fee, missing item data, or a
stated total that does not add up). A blocking issue returns a BLOCK
verdict instead of a quiet approval.

When a payment fails, PayGate does not auto-retry. It re-checks the
failed order, then proposes a retry capture — each step waits on a
separate, explicit human approval, logged in an append-only audit trail
protected by a SHA-256 hash chain.

Honest limits: the demo runs on clearly-labelled mock data. The real
PayPal path talks only to the PayPal sandbox, and it has NOT been
live-tested yet (no PayPal Developer account exists as of 2026-10-29).
Built with Python standard library only. No real payments are made.

Try it in under 15 minutes: python -m pytest -q, then ./DEMO.sh
(PayPal AI Hackathon project — submission NOT filed as of 2026-10-29.)

## Tags (suggested)

PayPal, AI agent, hackathon, checkout audit, agentic commerce,
consumer protection, audit trail, Python
