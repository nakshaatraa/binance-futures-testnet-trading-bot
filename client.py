"""
Low-level Binance Futures Testnet client.

Handles authentication (HMAC-SHA256), request signing, and
raw HTTP interactions. All API communication goes through here.
"""

from __future__ import annotations

import hashlib
import hmac
import time
from typing import Any, Dict, Optional
from urllib.parse import urlencode

import requests

from .logging_config import get_logger

logger = get_logger("client")

TESTNET_BASE_URL = "https://testnet.binancefuture.com"
RECV_WINDOW = 5000  # ms; how long the server accepts the request


class BinanceAPIError(Exception):
    """Raised when the Binance API returns an error response."""

    def __init__(self, code: int, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(f"Binance API error {code}: {message}")


class BinanceClient:
    """
    Thin wrapper around the Binance Futures REST API (USDT-M testnet).

    Responsibilities:
      - Sign requests with HMAC-SHA256
      - Attach the API key header
      - Surface HTTP / API errors as typed exceptions
      - Log every outbound request and inbound response at DEBUG level
    """

    def __init__(self, api_key: str, api_secret: str, base_url: str = TESTNET_BASE_URL) -> None:
        if not api_key or not api_secret:
            raise ValueError("API key and secret must both be non-empty strings.")
        self._api_key = api_key
        self._api_secret = api_secret.encode()
        self._base_url = base_url.rstrip("/")
        self._session = requests.Session()
        self._session.headers.update(
            {
                "X-MBX-APIKEY": self._api_key,
                "Content-Type": "application/x-www-form-urlencoded",
            }
        )
        logger.debug("BinanceClient initialised (base_url=%s)", self._base_url)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _sign(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Append timestamp + signature to a params dict (in-place) and return it."""
        params["timestamp"] = int(time.time() * 1000)
        params["recvWindow"] = RECV_WINDOW
        query_string = urlencode(params)
        signature = hmac.new(
            self._api_secret,
            query_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        params["signature"] = signature
        return params

    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        signed: bool = False,
    ) -> Any:
        """
        Execute an HTTP request and return the parsed JSON response.

        Raises:
            BinanceAPIError: on non-2xx or Binance error payload
            requests.RequestException: on network-level failures
        """
        params = params or {}
        if signed:
            params = self._sign(params)

        url = f"{self._base_url}{endpoint}"
        logger.debug("→ %s %s  params=%s", method.upper(), endpoint, params)

        try:
            if method.upper() in ("GET", "DELETE"):
                response = self._session.request(method, url, params=params, timeout=10)
            else:
                response = self._session.request(method, url, data=params, timeout=10)
        except requests.exceptions.ConnectionError as exc:
            logger.error("Network connection failed: %s", exc)
            raise
        except requests.exceptions.Timeout:
            logger.error("Request timed out: %s %s", method.upper(), endpoint)
            raise

        logger.debug(
            "← %s %s  status=%d  body=%s",
            method.upper(),
            endpoint,
            response.status_code,
            response.text[:500],  # truncate huge responses in logs
        )

        data = response.json()

        # Binance wraps errors in {"code": -XXXX, "msg": "..."}
        if isinstance(data, dict) and "code" in data and data["code"] != 200:
            raise BinanceAPIError(data["code"], data.get("msg", "Unknown error"))

        if not response.ok:
            response.raise_for_status()

        return data

    # ------------------------------------------------------------------
    # Public API methods
    # ------------------------------------------------------------------

    def ping(self) -> bool:
        """Return True if the testnet is reachable."""
        try:
            self._request("GET", "/fapi/v1/ping")
            return True
        except Exception:
            return False

    def get_exchange_info(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        """Fetch symbol metadata (tick size, step size, etc.)."""
        params = {}
        if symbol:
            params["symbol"] = symbol
        return self._request("GET", "/fapi/v1/exchangeInfo", params=params)

    def place_order(self, **order_params: Any) -> Dict[str, Any]:
        """
        POST /fapi/v1/order — place a new futures order.

        All parameters are forwarded as-is to the endpoint.
        Callers should pass validated, exchange-ready values.
        """
        logger.info(
            "Placing order: symbol=%s side=%s type=%s qty=%s price=%s",
            order_params.get("symbol"),
            order_params.get("side"),
            order_params.get("type"),
            order_params.get("quantity"),
            order_params.get("price", "N/A"),
        )
        return self._request("POST", "/fapi/v1/order", params=order_params, signed=True)

    def get_order(self, symbol: str, order_id: int) -> Dict[str, Any]:
        """Fetch an existing order by ID."""
        return self._request(
            "GET",
            "/fapi/v1/order",
            params={"symbol": symbol, "orderId": order_id},
            signed=True,
        )

    def cancel_order(self, symbol: str, order_id: int) -> Dict[str, Any]:
        """Cancel an open order."""
        return self._request(
            "DELETE",
            "/fapi/v1/order",
            params={"symbol": symbol, "orderId": order_id},
            signed=True,
        )

    def get_account(self) -> Dict[str, Any]:
        """Return current futures account information."""
        return self._request("GET", "/fapi/v2/account", signed=True)
