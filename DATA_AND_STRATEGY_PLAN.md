# StocksPlus — Data Sources & Strategy Expansion Plan

*Prepared June 2026. Research/setup notes, not financial advice. No strategy guarantees profit; backtests overstate live results; trade only on a paper account until proven.*

---

## First, the honest part: can we "analyze before it happens"?

No data feed gives you news *before* it's public — by the time a headline hits an API, the market has often already moved (algorithms react in milliseconds). Anyone selling "predict the market" is selling a fantasy. What *is* real and useful:

1. **Scheduled events known in advance.** Earnings dates, Fed (FOMC) meetings, CPI/jobs/GDP release dates are all on public calendars *ahead of time*. You can position and manage risk around them — that's the legitimate "before it happens."
2. **Speed.** Ingesting news/quotes fast and reacting quicker than a human can.
3. **Sentiment & leading indicators.** News sentiment, volume spikes, yield-curve and macro trends shift probabilities — they don't predict, they tilt the odds.
4. **Statistical edges.** Strategies that have a small, repeatable advantage over many trades (not a crystal ball on any single trade).

Build around reacting fast and managing risk around known events — not around foresight.

---

## Free APIs — what's actually free in 2026

### Price data (quotes / historical bars)

| API | Free limit | Real-time? | History | Notes |
|---|---|---|---|---|
| **yfinance** (Yahoo) | unofficial, no key | ~15-min delay | 20+ yrs daily | Free, huge coverage incl. Canada (.TO). Gets rate-limited/blocked sometimes — use as primary for backtests, add a fallback. |
| **Finnhub** | 60 calls/min | **Real-time US quotes** (`/quote`) | candles are premium | Best free real-time *quote*; no free historical candles. Great for live prices + news + calendars. |
| **Alpaca** | unlimited calls | real-time **IEX** feed (free) | yes (IEX) | Free real-time via IEX exchange; full SIP feed is paid. Pairs naturally with paper trading. |
| **Twelve Data** | 800 calls/day, 8/min | delayed | yes | Clean API, US + FX + crypto. Good fallback for bars. |
| **Alpha Vantage** | 25 calls/day, 5/min | 15-min delay | 20+ yrs | Very low daily cap; fine for occasional pulls + 50+ built-in indicators. |
| **Polygon / Massive** | 5 calls/min | delayed on free | 1 yr free (2003+ paid) | Excellent paid, thin free tier. |

**Recommended free stack for us:** `yfinance` for historical backtests (with Twelve Data as fallback), **Finnhub** for live US quotes + news + calendars, **Alpaca** for real-time IEX once we wire live paper trading.

### News & sentiment

| API | Free | Strength |
|---|---|---|
| **Finnhub news** | yes (60/min) | US company + general market news (already wired). Canadian company-news is premium. |
| **GDELT** | yes, unlimited, no key | Global news/event firehose — great for broad event detection. |
| **Marketaux** | free tier | International breadth, entity/ticker tagging, basic sentiment. |
| **Alpha Vantage News & Sentiment** | 25/day | Directional + magnitude sentiment per ticker. |
| **NewsData.io / NewsAPI** | free tier | General news search. |

### Scheduled events & macro (the "before it happens" layer)

| API | Free | Use |
|---|---|---|
| **Finnhub earnings calendar** | yes | Know upcoming earnings dates per ticker. |
| **Finnhub economic calendar** | yes | CPI, jobs, GDP, rate-decision dates + forecasts. |
| **FRED** (St. Louis Fed) | yes, free key | Gold-standard macro history: rates, yield curve, inflation, unemployment. Perfect for regime/leading-indicator signals. |
| **FMP economics** | free tier | Treasury yields, macro indicators, release calendar. |

---

## "What is history" — historical data, and why it matters

"History" = past price bars (open/high/low/close/volume) and past fundamentals/news. We use it to **backtest**: replay a strategy over years of real data to estimate how it would have behaved. Sources above give 20+ years of daily bars for free (yfinance, Alpha Vantage). Two rules:

- **More history = more honest.** Test across bull (2019, 2021), bear (2022), and choppy years, not just a recent uptrend.
- **History is not destiny.** A strategy that won 2015–2025 can still fail next year. Backtests rank ideas; they don't promise returns. Always paper-trade forward after backtesting.

---

## How we make this work on *any* stock + many strategies

Right now the engine tests a fixed 8-ticker basket. To analyze any stock and run many strategies, we add three pieces:

### 1. Universal data adapter (`engine/data_sources.py`)
One function `get_prices(ticker, period)` that tries yfinance first, falls back to Twelve Data / Alpha Vantage, and normalizes to the same format. Every strategy and the backtester call this — so adding any ticker "just works," US or Canadian.

### 2. Expanded strategy library (plug into the existing registry)
We already have momentum, breakout, mean-reversion. Easy additions, each a small file exposing `target_position(df)`:

- **MACD trend** — momentum via MACD line/signal cross.
- **Bollinger reversion** — buy lower band, sell middle/upper.
- **Volume breakout** — breakout confirmed by a volume surge.
- **Dual-momentum rotation** — hold whichever of a set (e.g. SPY vs bonds vs gold) has the strongest recent return; rotate monthly. (Historically strong for risk-managed growth.)
- **Sentiment overlay** — only take long signals when recent news sentiment isn't strongly negative (uses the news table).
- **Event filter** — avoid entering right before earnings (uses the earnings calendar).

### 3. A screener (`engine/screen.py`)
Scan a large universe (e.g. S&P 500 + TSX 60) every day, run the strategies, and write the **current top-ranked opportunities** to Supabase so the dashboard shows "what looks interesting today" — not just historical backtests.

### Dashboard additions
- An **"Opportunities" page**: today's ranked signals across the universe.
- An **"Events" page**: upcoming earnings + macro releases for your watchlist (the legitimate look-ahead).
- A **param-sweep view**: compare strategy settings side by side.

---

## Suggested build order
1. `data_sources.py` (universal adapter + fallback) — unlocks "any stock."
2. Add 3–4 more strategies to the registry.
3. `screen.py` — daily ranked opportunities across a big universe → Supabase.
4. Add an FRED + Finnhub-calendar pull for the Events page.
5. Schedule the daily refresh (so the dashboard stays current on its own).
6. Wire sentiment/event filters into strategies once the data is flowing.

Everything stays paper/research until a strategy proves itself forward over weeks.

---

## Reality check
- Free tiers are for research and paper trading, not low-latency live trading at scale.
- A strategy that looks great in backtest usually looks worse live (fees, slippage, latency, overfitting). The screener and backtester are for *ranking and filtering ideas*, then validating forward on paper.
- Diversification of strategies and strict risk limits matter more than any single "best" strategy.
