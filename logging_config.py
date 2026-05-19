"""
Logging configuration for the trading bot.
Sets up both file and console handlers with appropriate formatting.
"""

import logging
import sys
from pathlib import Path


LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_FILE = LOG_DIR / "trading_bot.log"

_configured = False


def setup_logging(level: str = "INFO") -> logging.Logger:
    """
    Configure root logger with file + console handlers.
    Safe to call multiple times — only configures once.
    """
    global _configured
    if _configured:
        return logging.getLogger("trading_bot")

    LOG_DIR.mkdir(exist_ok=True)

    numeric_level = getattr(logging, level.upper(), logging.INFO)

    root = logging.getLogger("trading_bot")
    root.setLevel(logging.DEBUG)  # capture everything; handlers filter

    # --- file handler (DEBUG+) ---
    file_fmt = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(file_fmt)

    # --- console handler (INFO+ by default) ---
    console_fmt = logging.Formatter(
        fmt="%(levelname)-8s %(message)s",
    )
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(numeric_level)
    ch.setFormatter(console_fmt)

    root.addHandler(fh)
    root.addHandler(ch)

    _configured = True
    return root


def get_logger(name: str) -> logging.Logger:
    """Return a child logger under the trading_bot namespace."""
    return logging.getLogger(f"trading_bot.{name}")
