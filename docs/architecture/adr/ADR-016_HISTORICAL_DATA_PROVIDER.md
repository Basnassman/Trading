# ADR-016: Historical Data Provider

**Status:** Accepted

**Date:** 2026-08-31

**Context:**
PHASE 22 mentioned `HistoricalDataProvider` as a separate interface. PHASE 23 implemented only 4 provider interfaces: MarketDataProvider, NewsProvider, MacroProvider, ExecutionProvider. Need to resolve whether HistoricalDataProvider is independent or part of MarketDataProvider.

**Decision:**
Historical data access is part of `MarketDataProvider`. No separate `HistoricalDataProvider` interface is needed.

**Rationale:**
- `MarketDataProvider.get_bars(symbol, timeframe, start, end)` already handles historical data
- `MarketDataProvider.get_ticks(symbol, start, end)` already handles historical ticks
- The same interface serves both real-time (subscribe_*) and historical (get_*) use cases
- A separate interface would duplicate method signatures
- Backtest vs Live differs by *adapter implementation*, not by interface

**Alternatives Considered:**
- Separate HistoricalDataProvider: Rejected — would duplicate get_bars/get_ticks signatures
- Split into StreamingProvider + HistoricalProvider: Rejected — adds complexity without benefit

**Consequences:**
- `MarketDataProvider` has both real-time (subscribe) and historical (get) methods
- Backtest adapter implements get_bars from database; MT5 adapter implements from broker
- No architectural deviation; this is consistent with Phase 23 implementation

**Note:**
This is NOT an error in Phase 23. Phase 23 correctly identified that historical data access belongs to MarketDataProvider.
