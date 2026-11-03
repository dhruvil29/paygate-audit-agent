# Demo storyboard — PayGate Audit Agent (< 3 minutes)

Video file: `demo/demo-video.mp4` (rendered from the REAL output of
`./DEMO.sh` — the frames show actual CLI output text, not a mockup
script. No live browser or screen recording was available in this
build environment, so frames were rendered from captured terminal
output with Pillow and encoded with ffmpeg. The live terminal version
is `./DEMO.sh`; run it to see the same output interactively.)

Actual video: 48 seconds, 8 frames at 6 seconds each (title + 6
transcript pages + close card).

| Time | Shot | What the viewer sees |
|---|---|---|
| 0:00–0:06 | Title | "PayGate Audit Agent — audit before you pay, never retry without a human." |
| 0:06–0:42 | Transcript | Real CLI output in order: clean checkout audit (PASS, itemized total math); flagged checkout audit (BLOCK — currency mismatch, missing item name, unusual fee, total mismatch, risky terms); gated recovery for the FAILED mock order (two separate approval gates, explicit demo approval logged, honest capture-failed result — the mock FAILED order cannot be captured, and the agent reports that instead of faking success); trail verification (hash chain intact). |
| 0:42–0:48 | Close | "Sandbox only. Mock by default. Human approves every retry." + repo run instructions. |

Narration note for the human uploading to YouTube: read the on-screen
verdict lines aloud; stress the two sentences that matter — "the agent
shows the math before payment" and "nothing retries without an explicit
approve, and every decision is logged."
