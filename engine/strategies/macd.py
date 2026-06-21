"""
MACD trend strategy.
  Long when the MACD line is above its signal line (uptrend momentum), else flat.
  MACD = EMA(12) - EMA(26);  signal = EMA(9) of MACD.
"""
from __future__ import annotations
import pandas as pd

FAST, SLOW, SIGNAL = 12, 26, 9


def target_position(df: pd.DataFrame, fast=FAST, slow=SLOW, signal=SIGNAL) -> pd.Series:
    close = df["close"]
    macd = close.ewm(span=fast, adjust=False).mean() - close.ewm(span=slow, adjust=False).mean()
    sig = macd.ewm(span=signal, adjust=False).mean()
    return (macd > sig).astype(float).fillna(0.0)
