"""Tests: mock labelling, sandbox-only real client, secret redaction."""

import os

import pytest

from paygate.paypal_client import (
    FakePayPalClient, PayPalAPIError, PayPalConfigError, RealPayPalClient,
    build_client, redact,
)


def test_mock_orders_are_labelled_mock():
    client = FakePayPalClient()
    assert client.source == "mock"
    order = client.get_order("MOCK-ORDER-OK")
    assert order["source"] == "mock"
    assert order["id"].startswith("MOCK-")


def test_mock_unknown_order_raises():
    with pytest.raises(PayPalAPIError):
        FakePayPalClient().get_order("MOCK-ORDER-NOPE")


def test_real_client_refuses_non_sandbox_url():
    with pytest.raises(PayPalConfigError):
        RealPayPalClient("id", "secret",
                         base_url="https://api-m.paypal.com")


def test_real_client_refuses_non_sandbox_mode(monkeypatch):
    monkeypatch.setenv("PAYPAL_MODE", "live")
    monkeypatch.setenv("PAYPAL_CLIENT_ID", "x")
    monkeypatch.setenv("PAYPAL_CLIENT_SECRET", "y")
    with pytest.raises(PayPalConfigError):
        RealPayPalClient.from_env()


def test_real_client_requires_credentials(monkeypatch):
    monkeypatch.setenv("PAYPAL_MODE", "sandbox")
    monkeypatch.delenv("PAYPAL_CLIENT_ID", raising=False)
    monkeypatch.delenv("PAYPAL_CLIENT_SECRET", raising=False)
    with pytest.raises(PayPalConfigError):
        RealPayPalClient.from_env()


def test_redact_strips_credential_shaped_values():
    cleaned = redact({"client_secret": "hunter2",
                      "order_id": "MOCK-1",
                      "nested": {"access_token": "abc"}})
    assert cleaned["client_secret"] == "[REDACTED]"
    assert cleaned["nested"]["access_token"] == "[REDACTED]"
    assert cleaned["order_id"] == "MOCK-1"


def test_build_client_kinds():
    assert build_client("mock").source == "mock"
    with pytest.raises(PayPalConfigError):
        build_client("bogus")
