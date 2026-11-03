# SUBMISSION.md — FINAL TEXT, NOT FILED on Devpost.

> Status 2026-11-03 (corrected): this text is ready to paste at filing time, but
> NOTHING has been filed. Devpost holds only an untitled draft
> (submission 1271672, 1/5 steps done, team only); the project
> submission itself is NOT filed. Do not paste this
> anywhere until the human-only steps at the bottom are done.

## Honest limits (stated, not hidden)

- The PayPal sandbox path is code-complete but NOT live-tested: no
  PayPal Developer account exists yet, so no live sandbox run has been
  made and no live sandbox result is claimed anywhere in this text.
- The default demo and all 22 tests run on clearly-labelled mock data.
- The demo video (48s, in `demo/demo-video.mp4`, decode-verified
  2026-10-29) is rendered from real CLI output of the mock-data demo;
  it is not footage of a live PayPal transaction.

## Project title

PayGate Audit Agent

## Text description (paste-ready)

PayGate Audit Agent audits a checkout BEFORE payment and refuses to
touch money without a human saying so.

Before you pay, it itemizes every fee, recomputes the total from the
line items, summarizes the terms, and flags anomalies: currency
mismatch, an unusual fee, missing item data, or a stated total that
does not add up. A blocking issue returns a BLOCK verdict instead of a
quiet approval.

When a payment fails, PayGate does not auto-retry. It re-checks the
failed order, then proposes a retry capture — and each step waits on a
separate, explicit human approval ("approve" or reject), logged in an
append-only audit trail. Rejection aborts the flow. There is no
auto-retry, no retry loop, and no way to skip the gate.

Every action is written to a JSONL audit trail (timestamp, action,
inputs, decision, approver, outcome) protected by a SHA-256 hash chain,
so the whole history can be verified with one command.

Built sandbox-only: the default demo runs on clearly-labelled mock
data, and the real PayPal path talks only to the PayPal sandbox
(`https://api-m.sandbox.paypal.com`, OAuth client-credentials, Orders
v2) with credentials from environment variables. The audit core is a
deterministic rule engine — same input, same verdict, every run — with
an optional local-LLM summarizer that stays disabled unless a local
Ollama server is actually present. Python standard library only; no
paid services, no paid APIs.

Try it in under 15 minutes: `python -m pytest -q`, then `./DEMO.sh`.

## Tools used

- PayPal REST API (Sandbox): OAuth 2.0 client-credentials flow, Orders
  v2 (create / get / capture) — real path; mock implementation for the
  default demo and tests
- Python 3 standard library (agent, CLI, audit trail)
- pytest (test suite, 22 tests)
- ffmpeg + Pillow (demo-video rendering only)
- Optional, local-only: Ollama (LLM summary rewording; disabled when
  absent — no cloud model is used)

## Links to fill in at filing time (do NOT invent these)

- Public GitHub repo URL: https://github.com/dhruvil29/paygate-audit-agent (MIT LICENSE shown, verified 2026-11-03)
- Hosted demo URL or repo run instructions: repo run instructions in
  README.md (functional demo, not a mockup)
- YouTube demo video URL (< 3 minutes): ________________ (human upload)

## Judging-criteria notes (for the filer, not for Devpost)

- Technological Implementation: deterministic audit engine, hash-chained
  trail, sandbox-pinned real client, 22 passing tests.
- Design: CLI-first, one-command demo, plain-language summaries.
- Potential Impact: pre-payment transparency + no silent retries is a
  real consumer-protection gap for agentic commerce.
- Innovation/Idea: the approval gate as a first-class, logged,
  unskippable part of the payment flow.
- Presentation: demo video under 3 minutes + storyboard in `demo/`.

## Human-only steps still owed (nothing below has been done)

1. Devpost sign-in + Official Rules acceptance (untitled draft on
   Devpost, submission 1271672, 1/5 steps; project submission NOT filed).
2. PayPal Developer account creation (then run the real sandbox path
   once and update this file with the result — until then, the
   sandbox-NOT-live-tested limit above stands).
3. YouTube demo video upload — package prepared in
   `demo/youtube-upload-package.md`; the upload itself is human-only
   and has NOT been done.
4. Final Submit click on Devpost — NOT done.
