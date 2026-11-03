"""Tests for the deterministic audit engine."""

from paygate.audit import Checkout, Item, audit_checkout


def _codes(report):
    return {f.code for f in report.findings}


def test_clean_checkout_passes():
    report = audit_checkout(Checkout(
        items=[Item(name="Widget", quantity=1, unit_price="24.99")],
        fees={"shipping": "5.00"}, tax="2.40", total="32.39",
        terms_text="Free returns within 30 days."))
    assert report.verdict == "PASS"
    assert report.computed_total == "32.39"


def test_currency_mismatch_blocks():
    report = audit_checkout(Checkout(
        items=[Item(name="Gadget", quantity=1, unit_price="20.00",
                    currency="EUR")]))
    assert report.verdict == "BLOCK"
    assert "CURRENCY_MISMATCH" in _codes(report)


def test_total_mismatch_blocks():
    report = audit_checkout(Checkout(
        items=[Item(name="Widget", quantity=1, unit_price="10.00")],
        total="99.99"))
    assert "TOTAL_MISMATCH" in _codes(report)
    assert report.verdict == "BLOCK"


def test_unusual_fee_warns_but_does_not_block():
    report = audit_checkout(Checkout(
        items=[Item(name="Widget", quantity=1, unit_price="10.00")],
        fees={"handling": "5.00"}, total="15.00",
        terms_text="Standard terms."))
    assert "UNUSUAL_FEE" in _codes(report)
    assert report.verdict == "WARN"


def test_missing_item_data_and_empty_cart():
    assert "MISSING_ITEM_DATA" in _codes(audit_checkout(Checkout(
        items=[Item(name="", quantity=1, unit_price="10.00")])))
    assert "EMPTY_CART" in _codes(audit_checkout(Checkout(items=[])))


def test_terms_summary_flags_risk_keywords():
    report = audit_checkout(Checkout(
        items=[Item(name="Widget", quantity=1, unit_price="10.00")],
        total="10.00",
        terms_text="This item is non-refundable. Final sale."))
    assert "TERMS_RISK_KEYWORD" in _codes(report)
    assert "non-refundable" in report.terms_summary


def test_terms_summary_is_deterministic():
    first = audit_checkout(Checkout(items=[], terms_text="Hello world."))
    second = audit_checkout(Checkout(items=[], terms_text="Hello world."))
    assert first.terms_summary == second.terms_summary
