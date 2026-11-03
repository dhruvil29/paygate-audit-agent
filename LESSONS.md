# LESSONS.md — PayGate Audit Agent build (2026-10-28)

## What worked

- Standard-library-only Python removed the whole dependency step:
  setup is "clone, run pytest, run DEMO.sh" with no pip install and
  no version conflicts. For a hackathon demo judged in minutes, that
  is worth more than any framework feature.
- Splitting the PayPal client into an interface + mock + real
  implementation made the human-only account step harmless: the demo,
  the tests, and the video all run on the mock, while the real path
  stays code-complete and sandbox-pinned for a credentialed judge.
- The approval gate as code (no `--yes` flag exists anywhere for
  money actions) is stronger than a policy note: the "cannot skip the
  gate" claim is testable, and the tests prove non-"approve" answers
  reject.
- Rendering the demo video from captured real CLI output (Pillow
  frames + ffmpeg) produced an honest under-3-minute video without a
  display or screen recorder. The storyboard states the method plainly
  instead of pretending it is a screencast.
- Verifying PayPal claims against two developer-docs pages (OAuth
  authentication + REST API URLs) before writing the client caught
  nothing wrong in the brief — but it confirmed the sandbox host and
  token endpoint independently of the brief's word.

## What failed / was blocked

- Real sandbox path never live-tested: no PayPal Developer account
  was created (human-only by design). Lesson: never let a build
  report imply a tested integration when only unit tests exist —
  README, SUBMISSION.md, and TEST-RUN.md all carry the same explicit
  "code-complete, not live-tested" sentence.
- First demo video was only 24 seconds / 4 frames because the scripted
  demo output is compact. Fix: render from the full transcript (clean
  audit + flagged audit + recovery + verify), which gave a fuller
  48-second video. Lesson: check the rendered duration against the
  storyboard before calling the video done.
- CLI global option placement tripped the first test version:
  `--trail` must precede the subcommand. Fix: tests were corrected
  (not the CLI), and the README documents the order. Lesson: put
  global options in the README example exactly as tested.
- Ollama is absent in this environment, so the LLM summarizer path is
  disabled. That is the designed fallback, but it means the "AI"
  story for judges currently rests on the deterministic engine alone.
  Lesson: pitch the determinism as the feature (reproducible verdicts
  before money moves), not as a placeholder for a model.

## What to reuse

- The hash-chained JSONL trail (`audit_trail.py`) is project-agnostic:
  any agent that needs a verifiable action log can copy it verbatim.
- The mock-vs-real client pattern (labelled mock ids, sandbox pinning,
  env-only credentials, `redact()` before logging) is a safe template
  for any future payment-API hackathon build.
- The "render video from real CLI output" recipe (Pillow + ffmpeg,
  storyboard states the method) works for any CLI-first demo where no
  screen recorder exists.
- The unusual-fee heuristic (30% of subtotal) is a guess with a
  documented threshold, not a rule — future work should calibrate it
  against real checkout data before presenting it to users as more
  than a flag.
