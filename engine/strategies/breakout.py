"""
Breakout strategy (Donchian channel).
  - ENTER long when price closes above the prior N-day high.
  - EXIT  when price closes below the prior M-day low.
Trend-following; aims to ride sustained moves.
"""
from __future__ import annotations
import pandas as pd
from ._util import position_from_signals

ENTRY_LOOKBACK = 20
EXIT_LOOKBACK = 10


def target_position(df: pd.DataFrame, entry=ENTRY_LOOKBACK, exit=EXIT_LOOKBACK) -> pd.Series:
    close = df["close"]
    hi = close.rolling(entry).max().shift(1)
    lo = close.rolling(exit).min().shift(1)
    entries = close > hi
    exits = close < lo
    return position_from_signals(entries, exits)
