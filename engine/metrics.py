"""Single source of truth for backtest metrics + equity curves."""
from __future__ import annotations
import numpy as np
import pandas as pd

TRADING_DAYS = 252


def _cagr(curve: pd.Series) -> float:
    years = len(curve) / TRADING_DAYS
    return float(curve.iloc[-1] ** (1 / years) - 1) if years > 0 else 0.0


def _mdd(curve: pd.Series) -> float:
    return float((curve / curve.cummax() - 1).min())


def _sharpe(ret: pd.Series) -> float:
    sd = ret.std()
    return float(ret.mean() / sd * np.sqrt(TRADING_DAYS)) if sd > 0 else 0.0


def evaluate(close: pd.Series, target_pos: pd.Series):
    """Returns (metrics_dict, strat_curve, bh_curve). Trades on the next bar."""
    pos = target_pos.shift(1).fillna(0.0)
    daily = close.pct_change().fillna(0.0)
    strat = daily * pos
    strat_curve = (1 + strat).cumprod()
    bh_curve = (1 + daily).cumprod()
    metrics = {
        "total_return": float(strat_curve.iloc[-1] - 1),
        "cagr": _cagr(strat_curve),
        "max_drawdown": _mdd(strat_curve),
        "sharpe": _sharpe(strat),
        "bh_total_return": float(bh_curve.iloc[-1] - 1),
        "bh_max_drawdown": _mdd(bh_curve),
        "bh_sharpe": _sharpe(daily),
        "trades": int((pos.diff().abs() > 0).sum()),
        "time_in_market": float(pos.mean()),
    }
    return metrics, strat_curve, bh_curve


def downsample_curves(strat_curve: pd.Series, bh_curve: pd.Series, n: int = 150) -> list[dict]:
    """Compact the curves to ~n points for fast charting."""
    step = max(1, len(strat_curve) // n)
    s = strat_curve.iloc[::step]
    b = bh_curve.iloc[::step]
    return [
        {"t": str(idx.date()), "strat": round(float(sv), 4), "bh": round(float(bv), 4)}
        for idx, sv, bv in zip(s.index, s.to_numpy(), b.to_numpy())
    ]
