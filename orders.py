"""
Order construction and placement logic.

This module sits between the CLI and the raw API client.
It translates validated user inputs into exchange-ready payloads,
calls the client, and returns a structured result object.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Dict, Optional

from .client import BinanceClient, BinanceAPIError
from .logging_config import get_logger

logger = get_logger("orders")


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------


@dataclass
class OrderResult:
    """Parsed, display-friendly representation of an exchange order response."""

    success: bool
    order_id: Optional[int] = None
    client_order_id: Optional[str] = None
    symbol: Optional[str] = None
    side: Optional[str] = None
    order_type: Optional[str] = None
    status: Optional[str] = None
    price: Optional[str] = None
    avg_price: Optional[str] = None
    orig_qty: Optional[str] = None
    executed_qty: Optional[str] = None
    time_in_force: Optional[str] = None
    raw: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None

    @classmethod
    def from_response(cls, data: Dict[str, Any]) -> "OrderResult":
        return cls(
            success=True,
            order_id=data.get("orderId"),
            client_order_id=data.get("clientOrderId"),
            symbol=data.get("symbol"),
            side=data.get("side"),
            order_type=data.get("type"),
            status=data.get("status"),
            price=data.get("price"),
            avg_price=data.get("avgPrice"),
            orig_qty=data.get("origQty"),
            executed_qty=data.get("executedQty"),
            time_in_force=data.get("timeInForce"),
            raw=data,
        )

    @classmethod
    def from_error(cls, message: str) -> "OrderResult":
        return cls(success=False, error_message=message)


# ---------------------------------------------------------------------------
# Order builder helpers
# ---------------------------------------------------------------------------


def _build_market_payload(symbol: str, side: str, quantity: Decimal) -> Dict[str, Any]:
    return {
        "symbol": symbol,
        "side": side,
        "type": "MARKET",
        "quantity": str(quantity),
    }


def _build_limit_payload(
    symbol: str,
    side: str,
    quantity: Decimal,
    price: Decimal,
    time_in_force: str = "GTC",
) -> Dict[str, Any]:
    return {
        "symbol": symbol,
        "side": side,
        "type": "LIMIT",
        "quantity": str(quantity),
        "price": str(price),
        "timeInForce": time_in_force,
    }


def _build_stop_market_payload(
    symbol: str,
    side: str,
    quantity: Decimal,
    stop_price: Decimal,
) -> Dict[str, Any]:
    return {
        "symbol": symbol,
        "side": side,
        "type": "STOP_MARKET",
        "quantity": str(quantity),
        "stopPrice": str(stop_price),
    }


# ---------------------------------------------------------------------------
# Public order functions
# ---------------------------------------------------------------------------


def place_market_order(
    client: BinanceClient,
    symbol: str,
    side: str,
    quantity: Decimal,
) -> OrderResult:
    """Place a MARKET order and return a structured result."""
    payload = _build_market_payload(symbol, side, quantity)
    return _execute(client, payload)


def place_limit_order(
    client: BinanceClient,
    symbol: str,
    side: str,
    quantity: Decimal,
    price: Decimal,
    time_in_force: str = "GTC",
) -> OrderResult:
    """Place a LIMIT order and return a structured result."""
    payload = _build_limit_payload(symbol, side, quantity, price, time_in_force)
    return _execute(client, payload)


def place_stop_market_order(
    client: BinanceClient,
    symbol: str,
    side: str,
    quantity: Decimal,
    stop_price: Decimal,
) -> OrderResult:
    """Place a STOP_MARKET order (bonus order type) and return a structured result."""
    payload = _build_stop_market_payload(symbol, side, quantity, stop_price)
    return _execute(client, payload)


# ---------------------------------------------------------------------------
# Internal execution wrapper
# ---------------------------------------------------------------------------


def _execute(client: BinanceClient, payload: Dict[str, Any]) -> OrderResult:
    """
    Call client.place_order, handle exceptions, and return an OrderResult.

    Keeps error handling in one place so each order type function stays clean.
    """
    try:
        response = client.place_order(**payload)
        result = OrderResult.from_response(response)
        logger.info(
            "Order accepted: id=%s symbol=%s status=%s executedQty=%s avgPrice=%s",
            result.order_id,
            result.symbol,
            result.status,
            result.executed_qty,
            result.avg_price,
        )
        return result

    except BinanceAPIError as exc:
        logger.error("API error placing order: code=%d msg=%s", exc.code, exc.message)
        return OrderResult.from_error(str(exc))

    except Exception as exc:
        logger.exception("Unexpected error placing order: %s", exc)
        return OrderResult.from_error(f"Unexpected error: {exc}")
