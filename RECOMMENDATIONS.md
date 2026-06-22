# StocksPlus — Honest Review: Gaps, Add/Remove, Priorities

*My candid engineering + trading-realism assessment. The app is a strong research/monitoring tool. It is NOT yet proven to make money, and a few things could give a false sense of confidence. Read this before risking capital.*

---

## What's genuinely good
- Clean data layer (US + Canada), 5 strategies, screener, fundamentals, backtests, a polished 6-page dashboard, and full automation. As a **research and monitoring** system it's well built.
- Honest disclaimers are present throughout. Good.

## The biggest gaps (most important first)

### 1. Nothing here is proven to make money yet
Backtests + a confidence score look authoritative, but **no signal has been validated forward**. Backtests overstate reality, and picking strategies by their best backtest is classic overfitting.
- **Add:** a **forward paper-trading tracker** — log every fresh signal with its date/price, then measure the *actual* forward return (1w/1m later) and hit-rate. This is the single most valuable next step; everything else is guesswork without it.

### 2. Backtests ignore costs
No commissions, slippage, or bid/ask spread are modeled — especially distorting for the volatile, low-priced Movers names where spreads are wide.
- **Add:** a fees + slippage assumption to `metrics.evaluate` (e.g., 0.05–0.2% per trade) so returns are realistic. High-trade strategies will look worse — correctly.

### 3. The confidence score and sentiment are heuristics, not validated
- The **confidence score** is a hand-tuned blend — it *looks* predictive but has never been checked against outcomes. Treat it as "setup tidiness," not probability of profit.
- **Sentiment** is a crude positive/negative keyword count. It misreads sarcasm, context, and neutral headlines. It's rough — label it as such (already softened) or upgrade to a real model later.

### 4. No risk-management layer
The screener/Movers flag *entries* but say nothing about **position size, stop-loss, or max exposure** — which is what actually determines whether you survive. Signals without sizing rules is how accounts blow up.
- **Add:** a simple risk helper — e.g., "risk 1% of capital, stop at -8%, so buy N shares," shown in the modal.

### 5. Single fragile data source
Everything depends on **yfinance**, which gets rate-limited/blocked and is unofficial. One outage and the whole pipeline stalls silently.
- **Add:** a fallback source (Stooq, Alpha Vantage, or Alpaca for US) and **failure alerting** (see #6).

### 6. No monitoring — failures are silent
If the VM cron errors (bad data, API change, expired key), you won't know; the dashboard just shows stale numbers.
- **Add:** an alert (email/Telegram) when a refresh fails, and a "last updated" freshness badge on each page so stale data is obvious.

### 7. The "day" horizon is borderline misleading
"Day trading" on end-of-day daily bars isn't really day trading. It's fine as *short-swing*, but the label implies more than the data supports.
- **Fix:** relabel as "short/medium/long swing," or wire Alpaca intraday bars before calling it day trading.

## What I'd consider removing / simplifying
- **Resist parameter-tuning** to chase prettier backtests — it's the fastest road to overfitting and real-money losses.
- **More strategies ≠ better.** Five is already plenty; adding more mostly adds noise and false confidence. Consider this feature-complete.
- **De-emphasize Movers** until validated — it's the riskiest surface and the confidence score is unproven there especially.

## Security / hygiene (minor)
- Repo is public with secrets gitignored — OK. Confirm `.env` on the VM is `chmod 600` and never committed.
- The anon key in the dashboard is fine (RLS read-only). The service-role key must stay only in `.env` (it does).

---

## Recommended priority order
1. **Forward paper-trading tracker** — prove (or disprove) the signals before any money. *Highest value.*
2. **Realistic backtests** (fees/slippage) + an out-of-sample / walk-forward split.
3. **Failure alerting + data-freshness badges** so you trust what you see.
4. **Data-source fallback** for resilience.
5. **Risk/position-sizing helper** in the UI.
6. **Then** IBKR paper execution (once the account clears) — close the loop on a *validated* strategy only.

## The one-sentence truth
You've built an excellent **decision-support and learning tool**; the remaining work is about **proving the signals work and controlling risk** — not adding more features. Treat every number as a hypothesis until the forward tracker says otherwise.
