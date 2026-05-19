"""
Input validation for order parameters.
All validation raises ValueError with actionable messages.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Optional


VALID_SIDES = {"BUY", "SELL"}
VALID_ORDER_TYPES = {"MARKET", "LIMIT", "STOP_MARKET"}


def validate_symbol(symbol: str) -> str:
    s = symbol.strip().upper()
    if not s:
        raise ValueError("Symbol cannot be empty.")
    if not s.isalnum():
        raise ValueError(f"Invalid symbol '{s}': must be alphanumeric (e.g. BTCUSDT).")
    return s


def validate_side(side: str) -> str:
    s = side.strip().upper()
    if s not in VALID_SIDES:
        raise ValueError(
            f"Invalid side '{side}'. Must be one of: {', '.join(sorted(VALID_SIDES))}."
        )
    return s


def validate_order_type(order_type: str) -> str:
    t = order_type.strip().upper()
    if t not in VALID_ORDER_TYPES:
        raise ValueError(
            f"Invalid order type '{order_type}'. "
            f"Must be one of: {', '.join(sorted(VALID_ORDER_TYPES))}."
        )
    return t


def validate_quantity(quantity: str | float) -> Decimal:
    try:
        qty = Decimal(str(quantity))
    except InvalidOperation:
        raise ValueError(f"Invalid quantity '{quantity}': must be a positive number.")
    if qty <= 0:
        raise ValueError(f"Quantity must be greater than zero, got {qty}.")
    return qty


def validate_price(price: Optional[str | float], order_type: str) -> Optional[Decimal]:
    """
    Price is required for LIMIT and STOP_MARKET orders.
    Returns None for MARKET orders (price is ignored by the exchange).
    """
    if order_type == "MARKET":
        if price is not None:
            # silently ignore — warn at call site if you want
            pass
        return None

    if price is None:
        raise ValueError(f"Price is required for {order_type} orders.")

    try:
        p = Decimal(str(price))
    except InvalidOperation:
        raise ValueError(f"Invalid price '{price}': must be a positive number.")

    if p <= 0:
        raise ValueError(f"Price must be greater than zero, got {p}.")

    return p


def validate_stop_price(
    stop_price: Optional[str | float], order_type: str
) -> Optional[Decimal]:
    """Stop price is required for STOP_MARKET orders."""
    if order_type != "STOP_MARKET":
        return None

    if stop_price is None:
        raise ValueError("Stop price (--stop-price) is required for STOP_MARKET orders.")

    try:
        sp = Decimal(str(stop_price))
    except InvalidOperation:
        raise ValueError(f"Invalid stop price '{stop_price}': must be a positive number.")

    if sp <= 0:
        raise ValueError(f"Stop price must be greater than zero, got {sp}.")

    return sp
