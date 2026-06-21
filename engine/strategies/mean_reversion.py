"""
Mean-reversion strategy (RSI).
  - ENTER long when RSI falls below `entry_below` (oversold).
  - EXIT  when RSI rises above `exit_above` (reverted to the mean).
Counter-trend; aims to buy dips and sell into recovery.
"""
from __future__ import annotations
import pandas as pd
from ._util import position_from_signals, rsi

RSI_PERIOD = 14
ENTRY_BELOW = 30
EXIT_ABOVE = 50


def target_position(df: pd.DataFrame, rsi_period=RSI_PERIOD,
                    entry_below=ENTRY_BELOW, exit_above=EXIT_ABOVE) -> pd.Series:
    r = rsi(df["close"], rsi_period)
    entries = r < entry_below
    exits = r > exit_above
    return position_from_signals(entries, exits)
