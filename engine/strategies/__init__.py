"""Strategy registry. Each strategy exposes target_position(df) -> 0/1 Series."""
from . import momentum, breakout, mean_reversion

REGISTRY = {
    "momentum": momentum.target_position,
    "breakout": breakout.target_position,
    "mean_reversion": mean_reversion.target_position,
}
