"""
Bollinger Band mean-reversion.
  ENTER long when price closes below the lower band (oversold).
  EXIT  when price closes back above the middle band (the SMA).
"""
from __future__ import annotations
import pandas as pd
from ._util import position_from_signals

WINDOW, NUM_STD = 20, 2.0


def target_position(df: pd.DataFrame, window=WINDOW, num_std=NUM_STD) -> pd.Series:
    close = df["close"]
    mid = close.rolling(window).mean()
    sd = close.rolling(window).std()
    lower = mid - num_std * sd
    entries = close < lower
    exits = close > mid
    return position_from_signals(entries, exits)
