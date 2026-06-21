"""
Universal price-data adapter.

get_prices(ticker, period="5y") -> DataFrame[open, high, low, close, volume]

Uses yfinance for BOTH US and Canadian (.TO / .V) tickers — free, covers the TSX,
20+ years of daily history. One source for all backtesting and screening.

Alpaca is optional, only for LIVE real-time US quotes later via get_quote().
"""
from __future__ import annotations
import pandas as pd
import config

_PERIOD_DAYS = {"1y": 365, "2y": 730, "3y": 1095, "5y": 1825, "10y": 3650, "max": 14600}
_COLS = ["open", "high", "low", "close", "volume"]


def _dates(period, start, end):
    if start:
        return pd.to_datetime(start), pd.to_datetime(end) if end else pd.Timestamp.today()
    days = _PERIOD_DAYS.get((period or "5y").lower(), 1825)
    end_d = pd.Timestamp.today()
    return end_d - pd.Timedelta(days=days), end_d


def get_prices(ticker, period="5y", start=None, end=None):
    """Daily OHLCV for any US or Canadian ticker, via yfinance."""
    import yfinance as yf
    s, e = _dates(period, start, end)
    raw = yf.download(ticker, start=s, end=e, auto_adjust=True, progress=False)
    if raw is None or raw.empty:
        return None
    if isinstance(raw.columns, pd.MultiIndex):
        raw.columns = raw.columns.get_level_values(0)
    raw = raw.rename(columns=str.lower)
    have = [c for c in _COLS if c in raw.columns]
    return raw[have].dropna()


def get_quote(ticker):
    """Latest price. Alpaca (real-time IEX) for US if keys set, else yfinance."""
    is_canadian = ticker.upper().endswith((".TO", ".V"))
    if not is_canadian and config.ALPACA_API_KEY and config.ALPACA_API_SECRET:
        try:
            from alpaca.data.historical import StockHistoricalDataClient
            from alpaca.data.requests import StockLatestQuoteRequest
            from alpaca.data.enums import DataFeed
            client = StockHistoricalDataClient(config.ALPACA_API_KEY, config.ALPACA_API_SECRET)
            q = client.get_stock_latest_quote(
                StockLatestQuoteRequest(symbol_or_symbols=ticker, feed=DataFeed.IEX))
            return float(q[ticker].ask_price or q[ticker].bid_price)
        except Exception as ex:
            print(f"  Alpaca quote failed for {ticker}: {ex} - using yfinance.")
    df = get_prices(ticker, period="1y")
    return float(df["close"].iloc[-1]) if df is not None and len(df) else None
