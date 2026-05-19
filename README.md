<div align="center">

<img src="https://img.shields.io/badge/Binance-Futures%20Testnet-F0B90B?style=for-the-badge&logo=binance&logoColor=black" />
<img src="https://img.shields.io/badge/Python-3.9%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" />
<img src="https://img.shields.io/badge/REST%20API-Direct-00D4AA?style=for-the-badge&logo=fastapi&logoColor=white" />
<img src="https://img.shields.io/badge/HMAC-SHA256-DC143C?style=for-the-badge&logo=letsencrypt&logoColor=white" />
<img src="https://img.shields.io/badge/License-MIT-22C55E?style=for-the-badge" />

<br /><br />

```
██████╗ ██╗███╗   ██╗ █████╗ ███╗   ██╗ ██████╗███████╗
██╔══██╗██║████╗  ██║██╔══██╗████╗  ██║██╔════╝██╔════╝
██████╔╝██║██╔██╗ ██║███████║██╔██╗ ██║██║     █████╗
██╔══██╗██║██║╚██╗██║██╔══██║██║╚██╗██║██║     ██╔══╝
██████╔╝██║██║ ╚████║██║  ██║██║ ╚████║╚██████╗███████╗
╚═════╝ ╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝╚═╝  ╚═══╝ ╚═════╝╚══════╝
           FUTURES TESTNET TRADING BOT
```

**A clean, production-structured Python trading bot for Binance USDT-M Futures Testnet.**  
Place `MARKET`, `LIMIT`, and `STOP_MARKET` orders via CLI — with HMAC-SHA256 request signing, structured dual-channel logging, and typed error handling.

<br />

[![Python](https://img.shields.io/badge/python-3.9%20|%203.10%20|%203.11%20|%203.12-blue)](https://www.python.org)
[![requests](https://img.shields.io/badge/deps-requests%20only-lightgrey)](https://pypi.org/project/requests/)
[![Testnet Only](https://img.shields.io/badge/⚠%20testnet-only-orange)](https://testnet.binancefuture.com)

</div>

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
- [Project Structure](#project-structure)
- [Setup](#setup)
- [Usage](#usage)
- [Order Types](#order-types)
- [Logging](#logging)
- [Error Handling](#error-handling)
- [Assumptions](#assumptions)

---

## Overview

This project was built as a take-home challenge for a Python Developer (Trading Bot) role.

The goal: interact with the Binance USDT-M Futures Testnet using direct REST calls — no SDK wrapper — with a clean layered architecture, proper request signing, and structured logging.

**What it does:**
- Places MARKET, LIMIT, and STOP_MARKET futures orders via a clean CLI
- Separates the API client layer from the command layer completely
- Validates all inputs before touching the network
- Logs every API request and response to a rotating file

**What it doesn't do:**
- Operate on live accounts (testnet only)
- Manage positions, leverage, or margin mode

---

## Architecture

Two clean layers with no bleed-through:

```
┌─────────────────────────────────────────────────────────────┐
│                         CLI LAYER                           │
│  cli.py                                                     │
│  • argparse subcommands: place / ping / account             │
│  • reads env vars — credentials never touch order logic     │
│  • calls validators.py before any network activity          │
│  • formats and prints OrderResult to console                │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                      ORDERS LAYER                           │
│  bot/orders.py                                              │
│  • one function per order type (market / limit / stop)      │
│  • builds exchange-ready payloads from validated inputs     │
│  • returns typed OrderResult dataclass — no raw dicts       │
│  • catches BinanceAPIError + generic exceptions here        │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                      CLIENT LAYER                           │
│  bot/client.py                                              │
│  • appends timestamp + recvWindow to every signed request   │
│  • HMAC-SHA256 signs the full query string                  │
│  • attaches X-MBX-APIKEY header via requests.Session        │
│  • raises typed BinanceAPIError on Binance error payloads   │
│  • logs every → request and ← response at DEBUG level       │
└─────────────────────────────────────────────────────────────┘
```

### Request Signing Flow

```
CLI args (symbol, side, qty, price)
         │
         ▼
   validators.py ──► ValueError if invalid
         │
         ▼
   orders.py  ──► build payload dict
         │
         ▼
   client._sign()
         │
         ├── params["timestamp"] = int(time.time() * 1000)
         ├── params["recvWindow"] = 5000
         ├── query_string = urlencode(params)
         └── signature = HMAC-SHA256(secret, query_string)
         │
         ▼
   POST https://testnet.binancefuture.com/fapi/v1/order
   Header: X-MBX-APIKEY: <api_key>
         │
         ▼
   JSON response ──► OrderResult dataclass ──► CLI prints it
```

---

## Features

| Feature | Detail |
|---|---|
| **Order types** | `MARKET`, `LIMIT` (GTC), `STOP_MARKET` |
| **Sides** | `BUY`, `SELL` |
| **Authentication** | HMAC-SHA256 signed requests, no SDK |
| **Input validation** | Symbol, side, type, quantity, price, stop price — all validated before any network call |
| **Typed errors** | `BinanceAPIError(code, message)`, network exceptions — all caught and surfaced cleanly |
| **Dual-channel logging** | `DEBUG` → file (full request/response bodies); `INFO` → console |
| **Subcommand CLI** | `place`, `ping`, `account` |
| **Minimal deps** | Only `requests` — no Binance SDK, no heavy frameworks |

---

## Project Structure

```
trading_bot/
│
├── bot/
│   ├── __init__.py
│   ├── client.py            ← Binance REST client: signing, HTTP, error surface
│   ├── orders.py            ← Order builders + OrderResult dataclass
│   ├── validators.py        ← Pure validation functions (no side effects)
│   └── logging_config.py    ← File + console logging configuration
│
├── cli.py                   ← CLI entry point (argparse subcommands)
│
├── logs/
│   └── trading_bot.log      ← Auto-created on first run
│
├── requirements.txt
└── README.md
```

---

## Setup

### 1 — Get Testnet API credentials

1. Visit [testnet.binancefuture.com](https://testnet.binancefuture.com) and sign in with GitHub
2. Navigate to the **API Key** section → click **Generate**
3. Copy your **API Key** and **Secret Key**

> ⚠️ The secret is shown only once. Save it before closing the page.

### 2 — Clone the repository

```bash
git clone https://github.com/nakshaatraa/binance-futures-testnet-trading-bot.git
cd binance-futures-testnet-trading-bot
```

### 3 — Create and activate a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate        # macOS / Linux
# .venv\Scripts\activate         # Windows
```

### 4 — Install dependencies

```bash
pip install -r requirements.txt
```

Single dependency: `requests >= 2.31.0`

### 5 — Configure credentials

**Option A — export inline:**

```bash
export BINANCE_TESTNET_API_KEY="your_api_key_here"
export BINANCE_TESTNET_API_SECRET="your_api_secret_here"
```

**Option B — `.env` file (recommended):**

```bash
# .env
export BINANCE_TESTNET_API_KEY="your_api_key_here"
export BINANCE_TESTNET_API_SECRET="your_api_secret_here"
```

```bash
source .env
```

> `.env` is listed in `.gitignore`. Never commit credentials to version control.

---

## Usage

### Check connectivity

```bash
python cli.py ping
```

```
INFO     Pinging Binance Futures Testnet... OK
```

---

### View account balances

```bash
python cli.py account
```

```
───────────────────────────────────────────────────────
  Account Overview
───────────────────────────────────────────────────────
  Total Wallet Balance  : 10000.00 USDT
  Total Unrealised PnL  : -2.34 USDT
  Available Balance     : 9850.22 USDT

  Assets with balance:
    USDT       wallet=10000.00000000
───────────────────────────────────────────────────────
```

---

### Place a MARKET order

```bash
python cli.py place --symbol BTCUSDT --side BUY --type MARKET --qty 0.01
```

```
───────────────────────────────────────────────────────
  Order Request Summary
───────────────────────────────────────────────────────
  Symbol     : BTCUSDT
  Side       : BUY
  Type       : MARKET
  Quantity   : 0.01
───────────────────────────────────────────────────────
  Order Response
───────────────────────────────────────────────────────
  Order ID   : 4059152775
  Cl. Ord ID : x-HNAaBJi4f2e1f3d5a6b
  Status     : FILLED
  Executed   : 0.01 / 0.01
  Avg Price  : 97241.50000
───────────────────────────────────────────────────────
  ✓ Order placed successfully.
───────────────────────────────────────────────────────
```

---

### Place a LIMIT order

```bash
python cli.py place --symbol BTCUSDT --side SELL --type LIMIT --qty 0.01 --price 99500
```

```
───────────────────────────────────────────────────────
  Order Request Summary
───────────────────────────────────────────────────────
  Symbol     : BTCUSDT
  Side       : SELL
  Type       : LIMIT
  Quantity   : 0.01
  Price      : 99500
───────────────────────────────────────────────────────
  Order Response
───────────────────────────────────────────────────────
  Order ID   : 4059154102
  Cl. Ord ID : x-HNAaBJi8c3a2b4f1e9d
  Status     : NEW
  Executed   : 0 / 0.01
  Avg Price  : N/A (market pending)
───────────────────────────────────────────────────────
  ✓ Order placed successfully.
───────────────────────────────────────────────────────
```

---

### Place a STOP_MARKET order

```bash
# Stop-loss: sell 0.01 BTC if price drops to 90,000
python cli.py place --symbol BTCUSDT --side SELL --type STOP_MARKET --qty 0.01 --stop-price 90000
```

---

### Verbose / debug mode

```bash
python cli.py --log-level DEBUG place --symbol BTCUSDT --side BUY --type MARKET --qty 0.01
```

Raw request params and response bodies are always captured to `logs/trading_bot.log`.  
`--log-level DEBUG` additionally mirrors them to the console.

---

### Full CLI reference

```
usage: trading_bot [-h] [--log-level {DEBUG,INFO,WARNING,ERROR}] command ...

subcommands:
  ping                  Check connectivity to the testnet
  account               Display current account balances
  place                 Place a new futures order

options for `place`:
  --symbol  SYM         Trading pair  (e.g. BTCUSDT, ETHUSDT)
  --side    SIDE        BUY or SELL
  --type    TYPE        MARKET | LIMIT | STOP_MARKET
  --qty     QTY         Order quantity
  --price   PX          Limit price   (required for LIMIT)
  --stop-price  SPX     Stop trigger  (required for STOP_MARKET)
```

---

## Order Types

### `MARKET`
Executes immediately at the best available price.

```
Required flags : --symbol --side --type --qty
Status returned: FILLED
avgPrice       : populated with actual fill price
```

### `LIMIT`
Rests on the order book until the market reaches your price. Default `timeInForce: GTC`.

```
Required flags : --symbol --side --type --qty --price
Status returned: NEW (resting) → FILLED (when hit)
avgPrice       : 0 until filled
```

### `STOP_MARKET` *(bonus order type)*
Triggers a market order when the last price crosses `stopPrice`. Typical stop-loss use case.

```
Required flags : --symbol --side --type --qty --stop-price
Status returned: NEW (waiting for trigger)
Triggers when : last price crosses stopPrice
```

---

## Logging

Logs are written to `logs/trading_bot.log` (directory is created automatically on first run).

| Level | Destination | Content |
|---|---|---|
| `DEBUG` | File only (default) | Full request params, raw response JSON body |
| `INFO` | File + console | Order placed, order accepted, ping results |
| `WARNING` | File + console | Input validation failures |
| `ERROR` | File + console | API errors, network failures |

**Sample log output:**

```log
2025-01-15 10:22:04 | DEBUG    | trading_bot.client | → POST /fapi/v1/order  params={'symbol': 'BTCUSDT', 'side': 'BUY', 'type': 'MARKET', 'quantity': '0.01', 'timestamp': 1736936524312, 'recvWindow': 5000, 'signature': 'a3f9c...redacted'}
2025-01-15 10:22:04 | DEBUG    | trading_bot.client | ← POST /fapi/v1/order  status=200  body={"orderId":4059152775,"status":"FILLED","avgPrice":"97241.50000",...}
2025-01-15 10:22:04 | INFO     | trading_bot.orders | Order accepted: id=4059152775 symbol=BTCUSDT status=FILLED executedQty=0.01 avgPrice=97241.50000
2025-01-15 10:22:31 | INFO     | trading_bot.orders | Order accepted: id=4059154102 symbol=BTCUSDT status=NEW executedQty=0 avgPrice=0
2025-01-15 10:25:48 | WARNING  | trading_bot.cli    | Validation error: Price is required for LIMIT orders.
2025-01-15 10:27:15 | ERROR    | trading_bot.orders | API error placing order: code=-2019 msg=Margin is insufficient.
```

---

## Error Handling

| Scenario | Where caught | Exit code |
|---|---|---|
| Missing API credentials | `cli.py` startup check | `2` |
| Invalid side (e.g. `LONG`) | `validators.py` | `2` |
| Negative or zero quantity | `validators.py` | `2` |
| LIMIT order without `--price` | `validators.py` | `2` |
| STOP_MARKET without `--stop-price` | `validators.py` | `2` |
| Binance API error (e.g. `-2019` insufficient margin) | `orders.py` → `BinanceAPIError` | `1` |
| Network timeout | `client.py` → `requests.Timeout` | `1` |
| Connection refused / DNS failure | `client.py` → `requests.ConnectionError` | `1` |

Validation errors produce no API call. All errors are logged before printing to the console.

---

## Assumptions

- **USDT-M perpetual contracts only** — not spot, not coin-margined futures.
- **`timeInForce` defaults to `GTC`** for all LIMIT orders. Change it in `bot/orders.py` if needed.
- **Quantity precision** must match the symbol's step size on the exchange. A `-1111` error means your quantity has too many decimal places for that symbol (e.g. use `0.001` BTC, not `0.0015`).
- **Leverage and margin mode** must be configured on the testnet web UI before placing orders — the bot does not set these.
- **Credentials via environment variables only** — they are never passed as CLI flags or hard-coded.

---

<div align="center">

Built for Binance Futures Testnet · Python 3.9+ · MIT License

</div>
