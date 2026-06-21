# StocksPlus — Strategies Guide

*Educational reference. Not financial advice. Backtests overstate live results; validate on paper before risking money.*

## How it all works (the short version)
Each strategy is a **rule** that decides when to hold a stock vs. stay in cash. The
system applies these rules to price data and shows you (a) how they did historically
(Backtests), (b) what they signal **today** across a universe (Opportunities), and
(c) the signals drawn on a price chart (Charts). News sentiment and a company-strength
score are shown alongside to help you judge each signal.

**How often things change:**
- Live prices: ~every 2 minutes during market hours.
- News + Opportunities: hourly, 7am–9pm ET weekdays.
- Backtests + fundamentals + charts: once daily (4:30pm ET) and Saturday.

**Do news and strategies move the picture?** Yes — signals recompute each refresh as
prices move, so the Opportunities list shifts hourly. News is context/filter today, not
an automatic trigger.

---

## The 5 strategies

### 1. Momentum (trend-following)
- **Idea:** ride established uptrends.
- **Rule:** hold long when the 20-day average price is above the 50-day average, unless RSI > 75 (too overbought). Otherwise cash.
- **Wins:** steady, sustained trends. **Loses:** choppy/sideways markets (whipsaws), and it lags at turning points.
- **Use it for:** large, trending names; as a "stay with the winners" filter.

### 2. Breakout (trend-following, Donchian)
- **Idea:** buy strength as it makes new highs.
- **Rule:** buy when price closes above its highest level of the prior 20 days; sell when it closes below the prior 10-day low.
- **Wins:** big sustained moves; cuts losers fast (low drawdowns). **Loses:** range-bound markets (false breakouts).
- **Use it for:** catching momentum early; tends to have the best risk-adjusted numbers in this set.

### 3. Mean-reversion (counter-trend, RSI)
- **Idea:** buy the dip, sell the recovery.
- **Rule:** buy when RSI < 30 (oversold); exit when RSI > 50 (recovered).
- **Wins:** range-bound markets and bounces; protected capital in the 2022 downturn. **Loses:** strong downtrends (catching a falling knife).
- **Use it for:** stable, quality names that oscillate rather than trend.

### 4. MACD (trend/momentum)
- **Idea:** act when momentum turns up.
- **Rule:** hold long when the MACD line (12-day EMA minus 26-day EMA) is above its 9-day signal line.
- **Wins:** trends; reacts a bit faster than the simple moving-average crossover. **Loses:** choppy markets (frequent flip-flops).
- **Use it for:** a quicker-reacting trend signal.

### 5. Bollinger (counter-trend, volatility)
- **Idea:** buy when price is statistically cheap.
- **Rule:** bands = 20-day average ± 2 standard deviations; buy when price closes below the lower band; exit when it returns to the average.
- **Wins:** mean-reverting, volatile names. **Loses:** sustained trends (price can hug a band).
- **Use it for:** volatility-aware dip buying.

**Families:** trend-followers = momentum, breakout, MACD (ride moves, sit out downtrends). Mean-reverters = RSI, Bollinger (buy weakness, sell into strength).

---

## What the numbers mean
- **Total return** — overall % gain/loss over the period.
- **CAGR** — that return expressed per year.
- **Max drawdown** — worst peak-to-trough drop; the "pain" measure.
- **Sharpe** — return per unit of risk. Above 1 is good; higher = smoother. Matters more than raw return.
- **Trades** — number of round-trips (more = more fees).
- **Time in market** — % of days holding vs. cash.
- **Buy & Hold** — benchmark of simply holding the stock.
- **Strength score** — 0–100 fundamentals quality (margins, ROE, growth, debt).
- **News mood** — average sentiment of recent headlines (−1 to +1).

## How to use the dashboard
1. **Opportunities** — today's buy signals. Filter to "Fresh buys only" and "Strong companies only" for a high-conviction shortlist; check the News mood column.
2. **Charts** — pick a ticker, choose a strategy's signals, and see exactly where it would buy/sell, with fundamentals below.
3. **Backtests** — confirm a strategy's historical behavior on that name (esp. the 2022 bear column for downside).
4. **News** — scan market-moving headlines.
5. **Overview** — live prices + the strategy leaderboard (which strategy is strongest on a risk-adjusted basis).

## Honest reminders
- These are mechanical rules, not predictions. No edge is guaranteed.
- High Sharpe + low drawdown beats chasing the highest return.
- Backtests flatter reality (no fees, slippage, latency). Paper-trade forward before real money.
- Diversifying across strategies and enforcing risk limits matters more than any single "best" strategy.
