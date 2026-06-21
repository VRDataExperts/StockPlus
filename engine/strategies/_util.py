"""Shared helpers for strategies."""
from __future__ import annotations
import pandas as pd


def position_from_signals(entries: pd.Series, exits: pd.Series) -> pd.Series:
    """Turn entry/exit booleans into a held 0/1 position series (long-only)."""
    pos = []
    state = 0
    for e, x in zip(entries.fillna(False).to_numpy(), exits.fillna(False).to_numpy()):
        if state == 0 and e:
            state = 1
        elif state == 1 and x:
            state = 0
        pos.append(float(state))
    return pd.Series(pos, index=entries.index, dtype=float)


def rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    rs = gain / loss.replace(0, pd.NA)
    return 100 - (100 / (1 + rs))
