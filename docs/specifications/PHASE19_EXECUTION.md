# PHASE 19 — EXECUTION

## XAUUSD Quantitative Trading System
## Mathematical & Engineering Specification

**Version:** 1.0.0-DRAFT
**Date:** 2026-08-31
**Status:** PENDING APPROVAL
**Classification:** Pre-Implementation — No Code

---

## A — OBJECTIVE

Define the **Execution** framework — the bridge between decision and real-world order placement.

This engine produces:
1. Broker/API integration specifications
2. Order type definitions
3. Order lifecycle management
4. Position modification protocols
5. Error handling and recovery
6. Duplicate order protection
7. Execution quality monitoring

**Critical Rule:** Execution only proceeds after Paper Trading success (Phase 18).

---

## B — BROKER/API INTEGRATION

### B.1 — Dual-Path Architecture

From existing codebase (`src/trading/mt5_connector.py`):

| Path | Method | Platform | Priority |
|------|--------|----------|----------|
| Primary | MetaTrader5 Python SDK | Windows | 1 (Highest) |
| Fallback | MetaAPI Cloud SDK | Cross-platform | 2 |

### B.2 — Connection Requirements

| Requirement | Specification |
|-------------|--------------|
| Authentication | Login + Password + Server |
| Connection Timeout | 10 seconds |
| Reconnection Attempts | 3 |
| Reconnection Delay | 5 seconds between attempts |
| Heartbeat | Every 30 seconds |
| Data Freshness | < 5 seconds latency |

### B.3 — Connection States

```
DISCONNECTED → CONNECTING → CONNECTED → SYNCHRONIZED
      ↑              ↓            ↓            ↓
      └──── RECONNECT ←── ERROR ←── TIMEOUT ←┘
```

| State | Description | Action |
|-------|-------------|--------|
| DISCONNECTED | No connection | Attempt connect |
| CONNECTING | Connection in progress | Wait |
| CONNECTED | Connection established | Wait for sync |
| SYNCHRONIZED | Ready for trading | Normal operation |
| ERROR | Connection error | Retry |
| TIMEOUT | Connection timed out | Retry with backoff |

---

## C — ORDER TYPES

### C.1 — Order Type Definitions

| Type | Code | Description | Use Case |
|------|------|-------------|----------|
| **Market Order** | ORDER_TYPE_BUY / ORDER_TYPE_SELL | Execute immediately at current price | Standard entry |
| **Limit Order** | ORDER_TYPE_BUY_LIMIT / ORDER_TYPE_SELL_LIMIT | Execute at specified price or better | Retest entry |
| **Stop Order** | ORDER_TYPE_BUY_STOP / ORDER_TYPE_SELL_STOP | Execute when price reaches level | BOS entry |

### C.2 — Order Selection Logic

$$\text{OrderType} = \begin{cases}
\text{Market} & \text{if trigger fired AND price at market} \\
\text{Limit} & \text{if waiting for retest at specific level} \\
\text{Stop} & \text{if waiting for break above/below level}
\end{cases}$$

### C.3 — Market Order

**When to Use:**
- Entry trigger has fired
- Immediate execution required
- Spread is within acceptable limits

**Parameters:**

```python
request = {
    "action": TRADE_ACTION_DEAL,
    "symbol": "XAUUSD",
    "volume": position_size_lots,
    "type": ORDER_TYPE_BUY,  # or ORDER_TYPE_SELL
    "price": current_price,  # Ask for buy, Bid for sell
    "magic": 20240419,       # Unique identifier
    "comment": f"AI:{algorithm}",
    "type_time": ORDER_TIME_GTC,
    "type_filling": ORDER_FILLING_IOC,
    "sl": stop_loss_price,
    "tp": take_profit_price
}
```

### C.4 — Limit Order

**When to Use:**
- Waiting for retest at specific level
- Better entry price desired
- Reduce slippage

**Parameters:**

```python
request = {
    "action": TRADE_ACTION_PENDING,
    "symbol": "XAUUSD",
    "volume": position_size_lots,
    "type": ORDER_TYPE_BUY_LIMIT,
    "price": retest_level,   # Desired entry price
    "sl": stop_loss_price,
    "tp": take_profit_price,
    "magic": 20240419,
    "comment": f"AI:{algorithm}:LIMIT"
}
```

### C.5 — Stop Order

**When to Use:**
- Waiting for breakout above/below level
- Confirm direction before entry

**Parameters:**

```python
request = {
    "action": TRADE_ACTION_PENDING,
    "symbol": "XAUUSD",
    "volume": position_size_lots,
    "type": ORDER_TYPE_BUY_STOP,
    "price": breakout_level,  # Trigger price
    "sl": stop_loss_price,
    "tp": take_profit_price,
    "magic": 20240419,
    "comment": f"AI:{algorithm}:STOP"
}
```

---

## D — ORDER LIFECYCLE

### D.1 — Lifecycle States

```
CREATED → VALIDATED → SUBMITTED → ACCEPTED → FILLED
                                  ↓
                              REJECTED → LOGGED
                                  ↓
                              PENDING → EXPIRED / FILLED / CANCELLED
```

### D.2 — Lifecycle Management

| State | Description | Action |
|-------|-------------|--------|
| CREATED | Order object created | Validate parameters |
| VALIDATED | All checks passed | Submit to broker |
| SUBMITTED | Sent to broker | Wait for response |
| ACCEPTED | Broker accepted | Wait for fill |
| FILLED | Order executed | Log and update position |
| REJECTED | Broker rejected | Log reason; retry if retriable |
| PENDING | Limit/Stop order active | Monitor for fill or expiry |
| EXPIRED | Pending order expired | Cancel and log |
| CANCELLED | User/system cancelled | Log reason |

### D.3 — Order Validation Checklist

Before submission:

| Check | Condition | Action if Fail |
|-------|-----------|---------------|
| Symbol | Valid and tradable | Reject |
| Volume | Within min/max limits | Adjust and retry |
| Price | Positive and reasonable | Reject |
| SL/TP | Correct side of price | Reject |
| Spread | Within acceptable limit | Reject or wait |
| Margin | Sufficient margin | Reduce size or reject |
| Market hours | Market is open | Queue for next open |

---

## E — POSITION MODIFICATION

### E.1 — SL/TP Modification

**When to Modify:**
- Break-even triggered (Phase 13)
- Trailing stop update (Phase 13)
- TP level reached (partial close)
- Emergency adjustment

**Modification Request:**

```python
request = {
    "action": TRADE_ACTION_SLTP,
    "symbol": "XAUUSD",
    "position": position_ticket,
    "sl": new_stop_loss,
    "tp": new_take_profit
}
```

### E.2 — SL Modification Rules

| Rule | Description |
|------|-------------|
| R1 | SL can only move **in favor** (closer to profit) |
| R2 | SL can **never** move against the position |
| R3 | SL modification is logged with timestamp |
| R4 | Failed SL modification triggers retry |

### E.3 — Partial Close

**When to Partial Close:**
- TP₁ reached → Close 50%
- TP₂ reached → Close 30% of remaining
- Emergency → Close all

**Partial Close Request:**

```python
request = {
    "action": TRADE_ACTION_DEAL,
    "symbol": "XAUUSD",
    "volume": lots_to_close,  # Partial amount
    "type": ORDER_TYPE_SELL,  # Opposite of position
    "price": current_bid,     # Bid for closing long
    "position": position_ticket,
    "magic": 20240419,
    "comment": f"AI:TP1_PARTIAL"
}
```

---

## F — ERROR HANDLING

### F.1 — Error Categories

| Category | Errors | Action |
|----------|--------|--------|
| **Retriable** | Connection lost, timeout, temporary rejection | Retry up to 3 times |
| **Non-Retriable** | Invalid volume, invalid price, market closed | Log and abort |
| **Critical** | Account disabled, insufficient margin | Halt trading |

### F.2 — Retriable Error Handling

```python
MAX_RETRIES = 3
RETRY_DELAY = 2 seconds

for attempt in range(MAX_RETRIES):
    result = send_order(request)
    if result.success:
        return result
    elif result.is_retriable:
        sleep(RETRY_DELAY)
        continue
    else:
        log_error(result)
        return None

log_error("Max retries exceeded")
return None
```

### F.3 — Non-Retriable Errors (from Phase 1)

| Error Code | Description | Action |
|-----------|-------------|--------|
| 10014 | Invalid volume | Adjust and retry once |
| 10015 | Invalid price | Reject |
| 10016 | Invalid stops | Adjust SL/TP |
| 10018 | Market closed | Queue for next open |
| 10019 | No money | Halt trading |
| 10022 | Too many orders | Wait and retry |

### F.4 — Error Logging

Every error is logged with:

| Field | Description |
|-------|-------------|
| Error Code | Numeric code |
| Error Description | Human-readable |
| Request | Original order request |
| Timestamp | When error occurred |
| Attempt | Which retry attempt |
| Resolution | What was done |

---

## G — RECONNECTION

### G.1 — Reconnection Strategy

```
Connection Lost
    ↓
Wait 5 seconds
    ↓
Attempt Reconnect (Attempt 1)
    ├── Success → Resume trading
    └── Fail →
        ↓
Wait 10 seconds
    ↓
Attempt Reconnect (Attempt 2)
    ├── Success → Resume trading
    └── Fail →
        ↓
Wait 20 seconds
    ↓
Attempt Reconnect (Attempt 3)
    ├── Success → Resume trading
    └── Fail →
        ↓
HALT TRADING
Alert operator
```

### G.2 — Post-Reconnection Actions

| Action | Description |
|--------|-------------|
| Verify connection | Confirm connection is stable |
| Check positions | Verify open positions match expected |
| Check pending orders | Verify pending orders status |
| Resume trading | Resume normal operation |
| Log reconnection | Record reconnection event |

### G.3 — Position Verification

After reconnection:

$$\text{Positions}_{\text{expected}} = \text{Positions}_{\text{before\_disconnect}}$$

$$\text{Positions}_{\text{actual}} = \text{GetPositions()}$$

If $\text{Positions}_{\text{expected}} \neq \text{Positions}_{\text{actual}}$:
- Log discrepancy
- Alert operator
- Do not resume trading until verified

---

## H — DUPLICATE ORDER PROTECTION

### H.1 — Problem

Without protection, the system might:
- Send the same order twice (network retry)
- Open multiple positions for the same signal
- Create conflicting orders

### H.2 — Protection Mechanisms

| Mechanism | Description |
|-----------|-------------|
| **Magic Number** | Unique identifier per strategy |
| **Order Deduplication** | Check for existing orders before sending |
| **Position Limit** | Max positions enforced |
| **Signal ID** | Each signal has unique ID |

### H.3 — Magic Number

$$\text{Magic} = 20240419$$

All orders from this system use the same magic number. This allows:
- Identifying system orders
- Preventing manual interference
- Tracking order history

### H.4 — Deduplication Check

Before sending an order:

$$\text{Duplicate} \iff \exists \, \text{order } o \in \text{OpenOrders}:$$

$$o.\text{symbol} = \text{request}.\text{symbol} \wedge o.\text{type} = \text{request}.\text{type} \wedge o.\text{magic} = \text{request}.\text{magic}$$

If duplicate detected:
- Cancel existing order
- Send new order
- Log replacement

### H.5 — Signal ID

Each decision from Phase 15 generates a unique signal ID:

$$\text{SignalID} = \text{DEC-YYYYMMDD-HHMMSS-NNN}$$

This ID is attached to the order and used for deduplication.

---

## I — EXECUTION QUALITY MONITORING

### I.1 — Metrics Tracked

| Metric | Definition | Target |
|--------|-----------|--------|
| Fill Rate | % of orders filled | > 95% |
| Avg Slippage | Average slippage per fill | < 1.0 pip |
| Avg Latency | Average order-to-fill time | < 1.0 sec |
| Requote Rate | % of requotes | < 5% |
| Rejection Rate | % of rejected orders | < 2% |
| Error Rate | % of failed orders | < 1% |

### I.2 — Quality Dashboard

```
=== EXECUTION QUALITY DASHBOARD ===
Period: Last 24 hours

Orders Submitted: 47
Orders Filled: 45 (95.7%) ✅
Orders Rejected: 1 (2.1%)
Orders Requoted: 2 (4.3%)

Avg Slippage: 0.65 pips ✅
Avg Latency: 0.38 sec ✅
Max Slippage: 2.1 pips
Max Latency: 1.2 sec

Connection Uptime: 99.8% ✅
Reconnections: 1
```

### I.3 — Quality Alerts

| Alert | Condition | Action |
|-------|-----------|--------|
| High Slippage | Avg > 1.5 pips | Alert; investigate |
| High Latency | Avg > 2.0 sec | Alert; check infrastructure |
| Low Fill Rate | < 90% | Alert; check broker |
| High Rejection Rate | > 5% | Alert; check order parameters |
| Connection Issues | > 3 reconnections/day | Alert; check network |

---

## J — EDGE CASES

### J.1 — Market Conditions

| Scenario | Handling |
|----------|----------|
| Market closed | Queue orders for next open |
| Holiday | No trading |
| Flash crash | Emergency halt |
| Gap through SL/TP | Execute at next available price |
| Spread spike | Wait or reject |

### J.2 — Order Issues

| Scenario | Handling |
|----------|----------|
| Partial fill | Accept partial; adjust remaining |
| Requote | Retry at new price (within tolerance) |
| Order expired | Cancel and log |
| Duplicate detected | Cancel old; send new |

### J.3 — Position Issues

| Scenario | Handling |
|----------|----------|
| Position not found after reconnection | Alert; manual verification |
| SL/TP not set correctly | Modify immediately |
| Partial close failed | Retry; alert if persistent |

---

## K — BIAS PREVENTION

### K.1 — Execution Bias

**Prevention:**
1. Orders executed at actual market price
2. No favorable fills assumed
3. Slippage measured realistically
4. Spread at execution time recorded

### K.2 — Latency Bias

**Prevention:**
1. Signal-to-execution latency measured
2. Entry at next bar open (backtest matches live)
3. No intra-bar execution assumed

---

## L — WHAT IS FIXED

### L.1 — Fixed at This Stage

| Item | Value | Rationale |
|------|-------|-----------|
| Primary Path | MetaTrader5 SDK | Existing integration |
| Fallback Path | MetaAPI Cloud | Cross-platform |
| Connection Timeout | 10 seconds | Reasonable |
| Reconnection Attempts | 3 | Conservative |
| Reconnection Delay | 5/10/20 seconds | Exponential backoff |
| Magic Number | 20240419 | Unique identifier |
| Max Retries | 3 | Prevent infinite loops |
| Retry Delay | 2 seconds | Between retries |
| Fill Rate Target | > 95% | High execution quality |
| Slippage Target | < 1.0 pip | Low execution cost |

### L.2 — Not Fixed (Deferred)

| Item | Deferred To |
|------|-------------|
| Optimal retry count | From live experience |
| Optimal retry delay | From live experience |
| Broker selection | From paper trading results |
| VPS selection | From latency requirements |

---

## M — WHAT REQUIRES TESTING

### M.1 — Hypotheses

| # | Hypothesis | Test Method | Expected |
|---|-----------|-------------|----------|
| H1 | Fill rate > 95% in live conditions | Monitor actual | > 95% |
| H2 | Slippage < 1.0 pip average | Monitor actual | < 1.0 pip |
| H3 | Latency < 1.0 second | Monitor actual | < 1.0 sec |
| H4 | Reconnection works reliably | Simulate disconnect | > 90% successful |
| H5 | Duplicate protection prevents double orders | Stress test | 0 duplicates |

### M.2 — Open Questions

| # | Question | Resolution |
|---|----------|------------|
| Q1 | Which broker provides best execution? | Test multiple brokers |
| Q2 | Is MetaAPI reliable enough for live? | Monitor during paper |
| Q3 | Should we use limit orders by default? | Test market vs. limit |
| Q4 | How to handle during news events? | Test news-specific execution |

---

## N — OUTPUT SCHEMA

### N.1 — Order Result

```python
@dataclass(frozen=True)
class OrderResult:
    """Result of an order submission."""
    
    # Order Details
    order_ticket: int
    signal_id: str
    symbol: str
    order_type: str                      # "market", "limit", "stop"
    direction: str                       # "buy" or "sell"
    volume: float
    
    # Execution
    status: str                          # "filled", "pending", "rejected"
    fill_price: float | None
    intended_price: float
    slippage: float | None
    
    # Timing
    submission_time: datetime
    fill_time: datetime | None
    latency_ms: float | None
    
    # SL/TP
    stop_loss: float
    take_profit: float
    
    # Costs
    spread: float
    commission: float
    
    # Error
    error_code: int | None
    error_description: str | None
    
    # Provenance
    provenance: DataProvenance
```

---

## O — DECISION OUTPUT

### O.1 — Order Execution

```
=== ORDER SUBMITTED ===
Signal ID: DEC-20260831-143000-001
Type: MARKET BUY
Volume: 1.67 lots
Intended Price: 1848.50

=== EXECUTION ===
Status: FILLED ✅
Fill Price: 1848.55
Slippage: +0.05 pips (acceptable)
Spread: 0.8 pips
Latency: 0.35 seconds

=== SL/TP ===
SL: 1842.50 (set)
TP₁: 1858.50 (set)
TP₂: 1868.50 (set)
TP₃: 1878.50 (set)

=== ORDER DETAILS ===
Ticket: 987654321
Magic: 20240419
Comment: AI:ensemble
```

### O.2 — Order Rejected

```
=== ORDER REJECTED ===
Signal ID: DEC-20260831-143500-002
Type: MARKET SELL
Volume: 1.67 lots

=== ERROR ===
Code: 10019
Description: Not enough money
Resolution: Halt trading; alert operator

=== ACTION ===
Trading halted
Operator notified via Telegram
```

---

## P — APPROVAL GATE

### The Phase 19 — Execution specification is now complete.

**Summary of what is defined:**

1. ✅ Dual-path broker integration (MT5 SDK + MetaAPI)
2. ✅ Connection states and management
3. ✅ Order types (Market, Limit, Stop)
4. ✅ Order lifecycle management
5. ✅ Position modification (SL/TP, partial close)
6. ✅ Error handling (retriable vs. non-retriable)
7. ✅ Reconnection strategy
8. ✅ Duplicate order protection
9. ✅ Execution quality monitoring
10. ✅ Edge cases and handling
11. ✅ Backtest requirements
12. ✅ Output schemas

---

### 📋 Points Requiring Your Approval:

1. **Dual-Path (MT5 + MetaAPI):** Acceptable architecture?

2. **Order Types (Market, Limit, Stop):** Sufficient?

3. **Reconnection (3 attempts, exponential backoff):** Appropriate?

4. **Duplicate Protection (Magic Number + Deduplication):** Sufficient?

5. **Error Handling (3 retries):** Appropriate?

6. **Execution Quality Targets:** Fill > 95%, Slippage < 1.0 pip, Latency < 1.0 sec?

7. **Position Verification after Reconnection:** Necessary?

8. **Magic Number (20240419):** Fixed identifier acceptable?

---

**Please review and approve (or request modifications) before I proceed to Phase 20 — Live.**

---

*Document generated as part of the XAUUSD Quantitative Trading System specification.*
*No code has been written. All definitions are mathematical/engineering specifications.*
