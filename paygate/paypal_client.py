"""PayPal client interface: one real sandbox client, one labelled mock.

REAL PATH (paypal_client.RealPayPalClient):
  - Base URL is pinned to the sandbox host. Any other host, or
    PAYPAL_MODE != "sandbox", raises PayPalConfigError before any call.
  - OAuth 2.0 client-credentials flow, per PayPal Developer docs:
    POST /v1/oauth2/token with HTTP Basic auth (client_id:secret),
    grant_type=client_credentials. Then Orders v2:
    POST /v2/checkout/orders, GET /v2/checkout/orders/{id},
    POST /v2/checkout/orders/{id}/capture.
  - Credentials come ONLY from environment variables
    PAYPAL_CLIENT_ID / PAYPAL_CLIENT_SECRET. They are never logged,
    never written to the audit trail (see redact()), never in this repo.
  - Standard library only (urllib) so setup needs no pip install.
  - NOTE: the real path is code-complete but NOT live-tested in this
    build: no PayPal Developer account was created (human-only step).
    A judge with sandbox credentials can run it; until then the mock
    path is the default demo path. The README says exactly this.

MOCK PATH (paypal_client.FakePayPalClient):
  - Clearly-labelled fake data (order ids start with "MOCK-", every
    payload carries "source": "mock"). Used by tests and the default
    demo. Mock responses are NEVER presented as real PayPal responses.

Sources verified 2026-10-28 (2+ PayPal Developer docs pages):
  - developer.paypal.com/api/rest/authentication (OAuth flow, sandbox
    token URL https://api-m.sandbox.paypal.com/v1/oauth2/token)
  - developer.paypal.com REST API URLs page (sandbox base URL table)
"""

from __future__ import annotations

import base64
import json
import os
import urllib.error
import urllib.request

SANDBOX_BASE_URL = "https://api-m.sandbox.paypal.com"
SENSITIVE_KEYS = ("client_id", "client_secret", "secret", "password",
                  "authorization", "access_token", "token")


class PayPalConfigError(Exception):
    pass


class PayPalAPIError(Exception):
    pass


def redact(obj):
    """Recursively replace credential-shaped values with '[REDACTED]'."""
    if isinstance(obj, dict):
        return {k: ("[REDACTED]" if k.lower() in SENSITIVE_KEYS
                    or "secret" in k.lower() or "token" in k.lower()
                    else redact(v))
                for k, v in obj.items()}
    if isinstance(obj, list):
        return [redact(v) for v in obj]
    return obj


class PayPalClient:
    """Interface both implementations satisfy."""

    source = "unknown"

    def get_order(self, order_id: str) -> dict:
        raise NotImplementedError

    def create_order(self, checkout: dict) -> dict:
        raise NotImplementedError

    def capture_order(self, order_id: str) -> dict:
        raise NotImplementedError


class RealPayPalClient(PayPalClient):
    source = "real-sandbox"

    def __init__(self, client_id: str, client_secret: str,
                 base_url: str = SANDBOX_BASE_URL):
        if base_url.rstrip("/") != SANDBOX_BASE_URL:
            raise PayPalConfigError(
                f"Refusing non-sandbox base URL: {base_url!r}. "
                f"Only {SANDBOX_BASE_URL} is allowed.")
        if not client_id or not client_secret:
            raise PayPalConfigError(
                "Missing credentials: set PAYPAL_CLIENT_ID and "
                "PAYPAL_CLIENT_SECRET environment variables.")
        self._client_id = client_id
        self._client_secret = client_secret
        self._base_url = SANDBOX_BASE_URL
        self._token: str | None = None

    @classmethod
    def from_env(cls) -> "RealPayPalClient":
        mode = os.environ.get("PAYPAL_MODE", "sandbox").lower()
        if mode != "sandbox":
            raise PayPalConfigError(
                f"Refusing PAYPAL_MODE={mode!r}: only 'sandbox' is "
                "supported by this project.")
        return cls(os.environ.get("PAYPAL_CLIENT_ID", ""),
                   os.environ.get("PAYPAL_CLIENT_SECRET", ""))

    def _access_token(self) -> str:
        if self._token:
            return self._token
        creds = base64.b64encode(
            f"{self._client_id}:{self._client_secret}".encode()).decode()
        req = urllib.request.Request(
            f"{self._base_url}/v1/oauth2/token",
            data=b"grant_type=client_credentials",
            headers={"Authorization": f"Basic {creds}",
                     "Content-Type": "application/x-www-form-urlencoded",
                     "Accept": "application/json"},
            method="POST")
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                payload = json.loads(resp.read())
        except urllib.error.HTTPError as exc:
            raise PayPalAPIError(
                f"PayPal token request failed: HTTP {exc.code}") from exc
        self._token = payload["access_token"]
        return self._token

    def _call(self, method: str, path: str, body: dict | None = None) -> dict:
        req = urllib.request.Request(
            f"{self._base_url}{path}",
            data=json.dumps(body).encode() if body is not None else None,
            headers={"Authorization": f"Bearer {self._access_token()}",
                     "Content-Type": "application/json"},
            method=method)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read() or b"{}")
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode(errors="replace")[:500]
            raise PayPalAPIError(
                f"PayPal {method} {path} failed: HTTP {exc.code}: "
                f"{detail}") from exc

    def get_order(self, order_id: str) -> dict:
        return self._call("GET", f"/v2/checkout/orders/{order_id}")

    def create_order(self, checkout: dict) -> dict:
        units = [{
            "amount": {
                "currency_code": checkout.get("currency", "USD"),
                "value": str(checkout.get("total", "0.00")),
            },
        }]
        return self._call("POST", "/v2/checkout/orders",
                          {"intent": "CAPTURE",
                           "purchase_units": units})

    def capture_order(self, order_id: str) -> dict:
        return self._call("POST",
                          f"/v2/checkout/orders/{order_id}/capture", {})


class FakePayPalClient(PayPalClient):
    """Clearly-labelled fake sandbox. No network calls, ever."""

    source = "mock"

    def __init__(self):
        self._orders = {
            "MOCK-ORDER-OK": {
                "id": "MOCK-ORDER-OK", "source": "mock",
                "status": "APPROVED",
                "purchase_units": [{
                    "amount": {"currency_code": "USD", "value": "29.99"},
                    "items": [
                        {"name": "Mock Widget", "quantity": "1",
                         "unit_amount": {"currency_code": "USD",
                                         "value": "24.99"}}],
                }],
            },
            "MOCK-ORDER-FAILED": {
                "id": "MOCK-ORDER-FAILED", "source": "mock",
                "status": "FAILED",
                "failure_reason": "Mock decline: insufficient funds "
                                  "(simulated; no real payment attempted).",
                "purchase_units": [{
                    "amount": {"currency_code": "USD", "value": "49.99"},
                    "items": [
                        {"name": "Mock Gadget", "quantity": "1",
                         "unit_amount": {"currency_code": "USD",
                                         "value": "49.99"}}],
                }],
            },
        }

    def get_order(self, order_id: str) -> dict:
        order = self._orders.get(order_id)
        if order is None:
            raise PayPalAPIError(f"Mock order not found: {order_id}")
        return dict(order)

    def create_order(self, checkout: dict) -> dict:
        order_id = "MOCK-ORDER-CREATED"
        order = {"id": order_id, "source": "mock", "status": "CREATED",
                 "purchase_units": [{"amount": {
                     "currency_code": checkout.get("currency", "USD"),
                     "value": str(checkout.get("total", "0.00"))}}]}
        self._orders[order_id] = order
        return dict(order)

    def capture_order(self, order_id: str) -> dict:
        order = self.get_order(order_id)
        if order.get("status") == "FAILED":
            raise PayPalAPIError(
                "Mock capture refused: source order status is FAILED. "
                "Use the recovery flow with human approval instead.")
        captured = dict(order, status="COMPLETED", source="mock")
        self._orders[order_id] = captured
        return captured


def build_client(kind: str) -> PayPalClient:
    if kind == "mock":
        return FakePayPalClient()
    if kind == "real":
        return RealPayPalClient.from_env()
    raise PayPalConfigError(f"Unknown client kind: {kind!r} "
                            "(use 'mock' or 'real')")
