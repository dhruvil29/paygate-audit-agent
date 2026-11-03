# PayGate Audit Agent

**PayPal AI Hackathon 2026 — Track 1 build (draft, NOT submitted).**

A Python agent that audits a checkout **before** payment, and — when a
payment fails — runs a recovery flow in which **every** retry or payment
action waits on an explicit human approval, logged in an append-only
audit trail. Sandbox only. No live money ever moves.

## The problem

Shoppers approve a total they never itemized: a fee buried in the total,
a currency that quietly changed, a total that does not add up. And when
a payment fails, most agents just retry — touching money without asking.
PayGate does the opposite: it shows the math first, and it never retries
without a human saying "approve".

## What it does

1. **Pre-payment audit** — itemized fees, recomputed total vs. stated
   total, terms summary, and anomaly flags: currency mismatch, unusual
   fee (one fee line over 30% of the goods subtotal — a documented
   heuristic, not a PayPal rule), missing item data, empty cart,
   negative amounts, total mismatch, missing/risky terms.
2. **Human-gated recovery** — on a FAILED payment, the agent re-checks
   the order, then proposes a retry capture. Each step needs a separate
   explicit approval. Rejection aborts the flow and is logged. There is
   no auto-retry, no retry loop, no `--yes` flag for money actions.
3. **Append-only audit trail** — JSONL, one record per action with
   timestamp, action, inputs, decision, approver, outcome, plus a
   SHA-256 hash chain. `trail --verify` detects any tampered line.

## Setup and run (under 15 minutes, $0)

Requirements: Python 3.11+ only. No pip installs, no API keys, no
accounts needed for the default demo path.

```bash
cd paypal-paygate
python3 -m pytest -q            # 22 tests, ~1 second
./DEMO.sh                       # scripted end-to-end demo (mock data)
python3 -m paygate.cli audit --checkout examples/checkout-clean.json
python3 -m paygate.cli audit --checkout examples/checkout-flagged.json
# exit code 2 = BLOCK verdict (audit found a blocking issue)
python3 -m paygate.cli audit-order --order-id MOCK-ORDER-OK
python3 -m paygate.cli --trail audit-trail.jsonl recover --order-id MOCK-ORDER-FAILED
# ^ prompts interactively: type "approve" or anything else to reject
python3 -m paygate.cli --trail audit-trail.jsonl trail --verify
```

Note: `--trail` is a global option and goes **before** the subcommand.

## Mock vs. real — read this before judging

| Path | What it is | When it runs |
|---|---|---|
| Mock (`--client mock`, the default) | `FakePayPalClient`: in-process fake orders, ids start with `MOCK-`, every payload carries `"source": "mock"`. No network calls. | Tests, `DEMO.sh`, the demo video, and every example in this README. |
| Real sandbox (`--client real`) | `RealPayPalClient`: PayPal REST API, sandbox base URL `https://api-m.sandbox.paypal.com` only, OAuth 2.0 client-credentials flow, Orders v2 (create / get / capture). Standard library only. | Only when you set the env vars below. |

**The real path is code-complete but NOT live-tested in this build:**
no PayPal Developer account was created during the build (a human-only
step), so no real sandbox call has ever been made from this code. A
judge with sandbox credentials can run it; until then, treat every
"real" claim as code review, not a tested transaction. Mock responses
are never presented as real PayPal responses anywhere in this repo.

## Environment variables (real sandbox path only)

| Variable | Meaning |
|---|---|
| `PAYPAL_CLIENT_ID` | Sandbox app client ID (from a PayPal Developer account — human step) |
| `PAYPAL_CLIENT_SECRET` | Sandbox app secret. Never committed, never logged; `redact()` strips credential-shaped keys from trail inputs. |
| `PAYPAL_MODE` | Must be exactly `sandbox`. Anything else (`live`, …) is refused before any network call. |

```bash
export PAYPAL_MODE=sandbox
export PAYPAL_CLIENT_ID="your-sandbox-client-id"
export PAYPAL_CLIENT_SECRET="your-sandbox-secret"
python3 -m paygate.cli audit-order --order-id <real-sandbox-order-id> --client real
```

Live endpoints are refused in code: a non-sandbox base URL raises
`PayPalConfigError` before any request is built.

## The "AI" component, stated honestly

The core is a **deterministic rule-based audit engine** (`paygate/audit.py`):
same input, same verdict, every run — which is what you want before
money moves. A local-LLM summarizer (`paygate/summarizer.py`) is
**optional** and uses a $0 local route only: it tries a local Ollama
server (`http://localhost:11434`) and, when none is reachable, prints a
clear "LLM summarizer disabled" note instead of inventing output. In
this build environment Ollama is not installed, so the LLM path is
disabled and the deterministic summary is the complete output. No paid
API, no cloud model call, no API key exists anywhere in this project.

## Audit-trail format (JSONL, one record per line)

```json
{"timestamp": "2026-10-28T17:00:00+00:00", "action": "approval:retry-capture",
 "inputs": {"order_id": "MOCK-ORDER-FAILED"}, "decision": "approve",
 "approver": "demo-operator (explicit --approve-demo flag)",
 "outcome": "approved", "prev_hash": "000…", "entry_hash": "abc…"}
```

`prev_hash` links each record to the previous one; `entry_hash` is the
SHA-256 of the record. `trail --verify` recomputes the chain.

## Architecture

```
paygate/
  audit.py         deterministic audit engine + terms summarizer
  paypal_client.py PayPalClient interface; Real (sandbox) + Fake (mock)
  approval.py      human approval gate + gated recovery flow
  audit_trail.py   append-only JSONL trail + SHA-256 hash-chain verify
  summarizer.py    deterministic summary; optional local-Ollama rewording
  cli.py           audit / audit-order / recover / trail / demo commands
tests/             pytest suite (audit, gate+trail, client, CLI end-to-end)
examples/          checkout-clean.json (PASS) / checkout-flagged.json (BLOCK)
DEMO.sh            scripted demo run (mock data, explicit demo approval)
demo/              DEMO-STORYBOARD.md + demo-video.mp4 (rendered from real CLI output)
```

## Tools used

Python 3.12 standard library only (no third-party runtime dependencies),
pytest (test runner), ffmpeg + Pillow (demo-video rendering only, not
part of the agent). Sources: PayPal Developer docs — Authentication
(OAuth client-credentials, sandbox token URL) and REST API URLs (sandbox
base URL table) — plus the official Devpost page
(https://paypalaihackathon.devpost.com/) for hackathon requirements.

## Human-only steps (NOT done by this build)

Devpost sign-in, PayPal Developer account creation, Official Rules
acceptance, the final Submit click, and the YouTube video upload. See
`SUBMISSION.md` (draft text only) and the build report for the full list.

## License

MIT — see `LICENSE`. Copyright line reads "Copyright (c) 2026 Dhruvil";
the surname is intentionally left out pending confirmation (flagged for
the parent agent).
