#!/usr/bin/env python3
"""
cli.py — Command-line interface for the Binance Futures Testnet trading bot.

Usage examples:
  python cli.py place --symbol BTCUSDT --side BUY --type MARKET --qty 0.01
  python cli.py place --symbol BTCUSDT --side SELL --type LIMIT --qty 0.01 --price 95000
  python cli.py place --symbol BTCUSDT --side SELL --type STOP_MARKET --qty 0.01 --stop-price 85000
  python cli.py account
  python cli.py ping
"""

from __future__ import annotations

import argparse
import os
import sys
from decimal import Decimal

from bot.client import BinanceClient, BinanceAPIError
from bot.logging_config import setup_logging, get_logger
from bot.orders import (
    OrderResult,
    place_market_order,
    place_limit_order,
    place_stop_market_order,
)
from bot.validators import (
    validate_symbol,
    validate_side,
    validate_order_type,
    validate_quantity,
    validate_price,
    validate_stop_price,
)

logger = get_logger("cli")

# ANSI colours — degrade gracefully on Windows / non-tty
_USE_COLOUR = sys.stdout.isatty() and os.name != "nt"

def _c(text: str, code: str) -> str:
    return f"\033[{code}m{text}\033[0m" if _USE_COLOUR else text

GREEN   = lambda t: _c(t, "32")
RED     = lambda t: _c(t, "31")
YELLOW  = lambda t: _c(t, "33")
CYAN    = lambda t: _c(t, "36")
BOLD    = lambda t: _c(t, "1")
DIM     = lambda t: _c(t, "2")


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------


def _print_separator(char: str = "─", width: int = 55) -> None:
    print(DIM(char * width))


def _print_request_summary(
    symbol: str,
    side: str,
    order_type: str,
    qty: Decimal,
    price: Decimal | None,
    stop_price: Decimal | None,
) -> None:
    _print_separator()
    print(BOLD("  Order Request Summary"))
    _print_separator()
    print(f"  Symbol     : {CYAN(symbol)}")
    print(f"  Side       : {GREEN(side) if side == 'BUY' else RED(side)}")
    print(f"  Type       : {order_type}")
    print(f"  Quantity   : {qty}")
    if price is not None:
        print(f"  Price      : {price}")
    if stop_price is not None:
        print(f"  Stop Price : {stop_price}")
    _print_separator()


def _print_order_result(result: OrderResult) -> None:
    if result.success:
        print(BOLD("  Order Response"))
        _print_separator()
        print(f"  Order ID   : {result.order_id}")
        print(f"  Cl. Ord ID : {result.client_order_id}")
        print(f"  Status     : {YELLOW(result.status or 'N/A')}")
        print(f"  Executed   : {result.executed_qty} / {result.orig_qty}")
        avg = result.avg_price
        print(f"  Avg Price  : {avg if avg and float(avg) > 0 else 'N/A (market pending)'}")
        _print_separator()
        print(GREEN(BOLD("  ✓ Order placed successfully.")))
    else:
        _print_separator()
        print(RED(BOLD(f"  ✗ Order failed: {result.error_message}")))
    _print_separator()
    print()


# ---------------------------------------------------------------------------
# Sub-command handlers
# ---------------------------------------------------------------------------


def cmd_ping(client: BinanceClient, _args: argparse.Namespace) -> int:
    print("Pinging Binance Futures Testnet...", end=" ", flush=True)
    if client.ping():
        print(GREEN("OK"))
        logger.info("Ping successful")
        return 0
    else:
        print(RED("FAILED"))
        logger.error("Ping failed")
        return 1


def cmd_account(client: BinanceClient, _args: argparse.Namespace) -> int:
    try:
        data = client.get_account()
    except BinanceAPIError as exc:
        print(RED(f"Failed to fetch account: {exc}"))
        logger.error("Account fetch failed: %s", exc)
        return 1
    except Exception as exc:
        print(RED(f"Unexpected error: {exc}"))
        logger.exception("Account fetch unexpected error: %s", exc)
        return 1

    assets = [a for a in data.get("assets", []) if float(a.get("walletBalance", 0)) > 0]
    _print_separator()
    print(BOLD("  Account Overview"))
    _print_separator()
    print(f"  Total Wallet Balance  : {data.get('totalWalletBalance', 'N/A')} USDT")
    print(f"  Total Unrealised PnL  : {data.get('totalUnrealizedProfit', 'N/A')} USDT")
    print(f"  Available Balance     : {data.get('availableBalance', 'N/A')} USDT")
    if assets:
        print(f"\n  Assets with balance:")
        for a in assets:
            print(f"    {a['asset']:<10} wallet={a['walletBalance']}")
    _print_separator()
    print()
    return 0


def cmd_place(client: BinanceClient, args: argparse.Namespace) -> int:
    # --- validate inputs ---
    try:
        symbol     = validate_symbol(args.symbol)
        side       = validate_side(args.side)
        order_type = validate_order_type(args.type)
        qty        = validate_quantity(args.qty)
        price      = validate_price(args.price, order_type)
        stop_price = validate_stop_price(args.stop_price, order_type)
    except ValueError as exc:
        print(RED(f"Validation error: {exc}"))
        logger.warning("Validation error: %s", exc)
        return 2

    logger.info(
        "Order request: symbol=%s side=%s type=%s qty=%s price=%s stop=%s",
        symbol, side, order_type, qty, price, stop_price,
    )

    _print_request_summary(symbol, side, order_type, qty, price, stop_price)

    # --- dispatch by type ---
    if order_type == "MARKET":
        result = place_market_order(client, symbol, side, qty)
    elif order_type == "LIMIT":
        result = place_limit_order(client, symbol, side, qty, price)  # type: ignore[arg-type]
    elif order_type == "STOP_MARKET":
        result = place_stop_market_order(client, symbol, side, qty, stop_price)  # type: ignore[arg-type]
    else:
        print(RED(f"Unhandled order type: {order_type}"))
        return 2

    _print_order_result(result)
    return 0 if result.success else 1


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="trading_bot",
        description="Binance Futures Testnet trading bot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
examples:
  python cli.py ping
  python cli.py account
  python cli.py place --symbol BTCUSDT --side BUY  --type MARKET     --qty 0.01
  python cli.py place --symbol BTCUSDT --side SELL --type LIMIT       --qty 0.01 --price 95000
  python cli.py place --symbol BTCUSDT --side SELL --type STOP_MARKET --qty 0.01 --stop-price 85000
        """,
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Console log verbosity (default: INFO; file always captures DEBUG)",
    )

    sub = parser.add_subparsers(dest="command", metavar="command")
    sub.required = True

    sub.add_parser("ping",    help="Check connectivity to the testnet")
    sub.add_parser("account", help="Display current account balances")

    place = sub.add_parser("place", help="Place a futures order")
    place.add_argument("--symbol", required=True,  metavar="SYM",  help="Trading pair (e.g. BTCUSDT)")
    place.add_argument("--side",   required=True,  metavar="SIDE", help="BUY or SELL")
    place.add_argument("--type",   required=True,  metavar="TYPE", help="MARKET | LIMIT | STOP_MARKET")
    place.add_argument("--qty",    required=True,  metavar="QTY",  type=float, help="Order quantity")
    place.add_argument("--price",  default=None,   metavar="PX",   type=float, help="Limit price (LIMIT orders)")
    place.add_argument(
        "--stop-price", dest="stop_price", default=None, metavar="SPX",
        type=float, help="Stop trigger price (STOP_MARKET orders)",
    )

    return parser


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    setup_logging(args.log_level)

    api_key    = os.environ.get("BINANCE_TESTNET_API_KEY", "").strip()
    api_secret = os.environ.get("BINANCE_TESTNET_API_SECRET", "").strip()

    if not api_key or not api_secret:
        print(
            RED("Error: ") +
            "API credentials not found.\n"
            "Set BINANCE_TESTNET_API_KEY and BINANCE_TESTNET_API_SECRET "
            "as environment variables (or add them to a .env file and run "
            "`source .env`)."
        )
        return 2

    client = BinanceClient(api_key, api_secret)

    dispatch = {
        "ping":    cmd_ping,
        "account": cmd_account,
        "place":   cmd_place,
    }
    return dispatch[args.command](client, args)


if __name__ == "__main__":
    sys.exit(main())
