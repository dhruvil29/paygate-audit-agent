# TEST-RUN.md — PayGate Audit Agent

Run date: 2026-10-28 (America/Toronto). Environment: Python 3.12.3,
pytest 9.1.1, ffmpeg 8.1.2. No pip installs were needed (standard
library only, plus pytest for tests and Pillow for video rendering).

## Pytest suite — PASS

Command (from the repo root):

```
python3 -m pytest -q
```

Result (final run, also reproduced on every earlier run):

```
22 passed in 1.38s
```

Coverage by file:

- `tests/test_audit.py` (7 tests): clean PASS, currency mismatch,
  total mismatch, unusual-fee warning, missing item data / empty cart,
  terms risk keywords, deterministic terms summary.
- `tests/test_gate_and_trail.py` (5 tests): approval + rejection
  logging, non-"approve" answers rejected, recovery abort on rejection,
  honest capture-failed result for the mock FAILED order,
  no-recovery-needed for a non-FAILED order, tampered trail detected.
- `tests/test_paypal_client.py` (8 tests): mock labelling, unknown
  mock order error, non-sandbox URL refused, non-sandbox mode refused,
  missing credentials refused, secret redaction, client factory.
- `tests/test_cli.py` (3 tests): clean/flagged CLI audits (exit 0 / 2),
  scripted demo + trail verify, demo without approval does not recover.

## Demo run — PASS

```
./DEMO.sh   # exit 0
```

Verified in the output: clean audit PASS, flagged audit BLOCK,
recovery flow with two logged approvals, honest capture-failed result
for `MOCK-ORDER-FAILED`, and `OK: 6 entries, chain intact` from trail
verification. Full output was captured during the build; re-run
`./DEMO.sh` any time to reproduce it.

## Demo video — DONE, under 3 minutes

- File: `demo/demo-video.mp4`
- Duration: 48 seconds (ffprobe-verified), size 302,816 bytes.
- Method: frames rendered with Pillow from REAL concatenated CLI output
  (clean audit, flagged audit, gated recovery, trail verify), encoded
  with ffmpeg (libx264, yuv420p). No screen recording was available in
  this build environment; the live terminal equivalent is `./DEMO.sh`.
  See `demo/DEMO-STORYBOARD.md`.
- YouTube upload is HUMAN-ONLY and has NOT been attempted.

## Real PayPal sandbox path — NOT live-tested (stated, not hidden)

No PayPal Developer account was created during this build (human-only
step, per the brief). The real client code path (`RealPayPalClient`)
passes its unit tests (sandbox pinning, mode refusal, credential
requirement) but has never made a live network call. A judge with
sandbox credentials must run it once before any claim of a tested
sandbox transaction is made. The README and SUBMISSION.md say exactly
this.

## Secrets scan — CLEAN (one placeholder hit, explained)

Command (from the repo root):

```
grep -rniE 'api[_-]?key|apikey|client_secret\s*=\s*"[^" ]|password\s*=\s*"[^" ]|bearer [A-Za-z0-9._-]{10,}|sk-live|sk_live' .
```

Result: exactly one hit — `README.md`, the placeholder line
`export PAYPAL_CLIENT_SECRET="your-sandbox-secret"` (documentation
placeholder, not a credential). No real secret, key, token value, or
password exists anywhere in the repo. Credential variable *names*
(`PAYPAL_CLIENT_ID`, `PAYPAL_CLIENT_SECRET`) appear in code/docs as
`os.environ.get(...)` lookups and setup instructions only; test files
use dummy monkeypatched values `"x"` / `"y"`. No trail file is shipped
in the repo (trail files are git-ignored; demo trails were deleted
after the video render).

## LLM summarizer — disabled, as designed

No local Ollama server is reachable in this environment, so
`llm_summary()` returns None and the CLI prints the "LLM summarizer
disabled" note. The deterministic summary is the complete output. This
is the intended behaviour, not a failure.
