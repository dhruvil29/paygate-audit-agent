"""Summaries: deterministic first, local LLM only if actually present.

deterministic_summary() always works and is what the CLI prints by
default. llm_summary() tries a local Ollama server
(http://localhost:11434) and returns None when it is not reachable --
the caller then prints a clear "LLM summarizer disabled" note instead
of inventing AI output. No paid API, no API key, no cloud call, ever.
"""

from __future__ import annotations

import json
import urllib.request

from .audit import AuditReport


def deterministic_summary(report: AuditReport) -> str:
    errors = [f for f in report.findings if f.severity == "error"]
    warnings = [f for f in report.findings if f.severity == "warning"]
    lines = [f"Verdict: {report.verdict}.",
             f"Computed total {report.computed_total} "
             f"(goods {report.subtotal}, fees {report.fees}, "
             f"tax {report.tax})."]
    if report.stated_total is not None:
        lines.append(f"Stated total: {report.stated_total}.")
    if errors:
        lines.append("Blocking issues: " +
                     "; ".join(f.message for f in errors))
    if warnings:
        lines.append("Warnings: " + "; ".join(f.message for f in warnings))
    if not errors and not warnings:
        lines.append("No issues found.")
    lines.append(f"Terms: {report.terms_summary}")
    return " ".join(lines)


def llm_summary(report: AuditReport, model: str = "llama3.2") -> str | None:
    """Return an Ollama rewording, or None if Ollama is not reachable.

    Returns None (not an error, not a fake summary) when no local
    server answers within 3 seconds. The caller must say so plainly.
    """
    prompt = ("Reword this checkout audit in two plain sentences, "
              "changing no numbers:\n" + deterministic_summary(report))
    body = json.dumps({"model": model, "prompt": prompt,
                       "stream": False}).encode()
    req = urllib.request.Request(
        "http://localhost:11434/api/generate", data=body,
        headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=3) as resp:
            return json.loads(resp.read()).get("response")
    except Exception:
        return None
