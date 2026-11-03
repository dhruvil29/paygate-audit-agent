"""Deterministic pre-payment checkout audit engine.

This is the core "AI" of PayGate in the honest sense: a rule-based
analysis engine with fully reproducible output. There is no hidden model
call here. An optional local-LLM rewording layer lives in summarizer.py
and is disabled unless a local Ollama server is actually reachable.

Rules (each finding carries a stable code so tests and judges can
reproduce it):
  EMPTY_CART, MISSING_ITEM_DATA, CURRENCY_MISMATCH, TOTAL_MISMATCH,
  UNUSUAL_FEE, NEGATIVE_AMOUNT, TERMS_MISSING, TERMS_RISK_KEYWORD
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP

CENT = Decimal("0.01")
# A single fee line above 30% of the goods subtotal is unusual enough to
# flag. This threshold is a heuristic, documented here and in README.md;
# it is not a PayPal rule and is never presented as one.
UNUSUAL_FEE_RATIO = Decimal("0.30")
TOLERANCE = Decimal("0.01")

RISK_KEYWORDS = ("non-refundable", "no refund", "final sale",
                 "auto-renew", "subscription renews", "restocking fee")


def _money(value) -> Decimal:
    return Decimal(str(value)).quantize(CENT, rounding=ROUND_HALF_UP)


@dataclass
class Item:
    name: str = ""
    quantity: int = 1
    unit_price: str = "0.00"
    currency: str = "USD"

    def line_total(self) -> Decimal:
        return _money(self.unit_price) * int(self.quantity)


@dataclass
class Checkout:
    items: list = field(default_factory=list)
    currency: str = "USD"
    fees: dict = field(default_factory=dict)  # e.g. {"shipping": "5.00"}
    tax: str = "0.00"
    total: str | None = None  # stated total, if the caller supplies one
    terms_text: str = ""

    @classmethod
    def from_dict(cls, data: dict) -> "Checkout":
        items = [Item(**{k: v for k, v in it.items()
                         if k in ("name", "quantity", "unit_price",
                                  "currency")})
                 for it in data.get("items", [])]
        return cls(
            items=items,
            currency=data.get("currency", "USD"),
            fees=dict(data.get("fees", {})),
            tax=str(data.get("tax", "0.00")),
            total=(str(data["total"]) if data.get("total") is not None
                   else None),
            terms_text=data.get("terms_text", ""),
        )


@dataclass
class Finding:
    severity: str  # "error" | "warning" | "info"
    code: str
    message: str


@dataclass
class AuditReport:
    verdict: str  # PASS | WARN | BLOCK
    subtotal: str
    fees: dict
    tax: str
    computed_total: str
    stated_total: str | None
    findings: list
    terms_summary: str

    def to_dict(self) -> dict:
        return {
            "verdict": self.verdict,
            "subtotal": self.subtotal,
            "fees": self.fees,
            "tax": self.tax,
            "computed_total": self.computed_total,
            "stated_total": self.stated_total,
            "findings": [{"severity": f.severity, "code": f.code,
                          "message": f.message} for f in self.findings],
            "terms_summary": self.terms_summary,
        }


def summarize_terms(text: str) -> str:
    """Deterministic terms summary: keyword lines, else first sentence.

    No model is involved, so the summary is identical on every run.
    """
    if not text or not text.strip():
        return "No terms text supplied; nothing could be summarized."
    lowered = text.lower()
    hits = [kw for kw in RISK_KEYWORDS if kw in lowered]
    first = text.strip().split(".")[0].strip()
    if hits:
        return (f"Terms flag keywords present: {', '.join(hits)}. "
                f"Opening line: {first}.")
    return f"Terms opening line: {first}."


def audit_checkout(checkout: Checkout) -> AuditReport:
    findings: list[Finding] = []
    fees = {k: str(_money(v)) for k, v in checkout.fees.items()}

    if not checkout.items:
        findings.append(Finding("error", "EMPTY_CART",
                                "Checkout has no items."))
    subtotal = Decimal("0.00")
    for item in checkout.items:
        price = _money(item.unit_price)
        if not item.name.strip():
            findings.append(Finding("error", "MISSING_ITEM_DATA",
                                    "An item has no name."))
        if int(item.quantity) <= 0:
            findings.append(Finding("error", "MISSING_ITEM_DATA",
                                    f"Item {item.name!r} has quantity "
                                    f"{item.quantity}."))
        if price < 0:
            findings.append(Finding("error", "NEGATIVE_AMOUNT",
                                    f"Item {item.name!r} has a negative "
                                    f"price."))
        if item.currency != checkout.currency:
            findings.append(Finding("error", "CURRENCY_MISMATCH",
                                    f"Item {item.name!r} is priced in "
                                    f"{item.currency} but the checkout "
                                    f"currency is {checkout.currency}."))
        subtotal += price * int(item.quantity)
    subtotal = _money(subtotal)

    fee_total = sum((_money(v) for v in fees.values()), Decimal("0.00"))
    for name, value in fees.items():
        amount = _money(value)
        if amount < 0:
            findings.append(Finding("error", "NEGATIVE_AMOUNT",
                                    f"Fee {name!r} is negative."))
        elif subtotal > 0 and amount > subtotal * UNUSUAL_FEE_RATIO:
            findings.append(Finding("warning", "UNUSUAL_FEE",
                                    f"Fee {name!r} ({amount}) is over 30% "
                                    f"of the goods subtotal ({subtotal})."))
    tax = _money(checkout.tax)
    if tax < 0:
        findings.append(Finding("error", "NEGATIVE_AMOUNT", "Tax is negative."))
    computed = _money(subtotal + fee_total + tax)

    if checkout.total is not None:
        stated = _money(checkout.total)
        if abs(stated - computed) > TOLERANCE:
            findings.append(Finding("error", "TOTAL_MISMATCH",
                                    f"Stated total {stated} does not match "
                                    f"computed total {computed} "
                                    f"(subtotal {subtotal} + fees "
                                    f"{fee_total} + tax {tax})."))
    else:
        stated = None

    if not checkout.terms_text.strip():
        findings.append(Finding("warning", "TERMS_MISSING",
                                "No terms text supplied with the checkout."))
    elif any(kw in checkout.terms_text.lower() for kw in RISK_KEYWORDS):
        findings.append(Finding("warning", "TERMS_RISK_KEYWORD",
                                "Terms contain a buyer-risk keyword "
                                "(e.g. non-refundable / final sale)."))

    if any(f.severity == "error" for f in findings):
        verdict = "BLOCK"
    elif findings:
        verdict = "WARN"
    else:
        verdict = "PASS"
    return AuditReport(
        verdict=verdict,
        subtotal=str(subtotal),
        fees=fees,
        tax=str(tax),
        computed_total=str(computed),
        stated_total=(str(stated) if stated is not None else None),
        findings=findings,
        terms_summary=summarize_terms(checkout.terms_text),
    )
