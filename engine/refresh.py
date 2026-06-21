"""
Pipeline refresh. Run on an always-on machine (the VM) via cron.

    python engine/refresh.py          # FULL: fundamentals -> news -> backtests -> screener
    python engine/refresh.py light    # LIGHT: news -> screener  (for hourly intraday runs)

Backtests + fundamentals barely change intraday, so use 'light' hourly during
market hours and the full run once after close. One step failing won't stop the rest.
"""
from __future__ import annotations
import sys
import traceback


def _step(name, fn):
    print(f"\n===== {name} =====")
    try:
        fn()
    except Exception:
        print(f"[{name}] FAILED:")
        traceback.print_exc()


def main(light: bool):
    import news_ingest, screen
    if not light:
        import fundamentals, compare
        _step("fundamentals", lambda: fundamentals.main(dry=False))
    _step("news", lambda: news_ingest.main())
    if not light:
        _step("backtests", lambda: compare.main(dry=False))
    _step("screener", lambda: screen.main(dry=False))
    print(f"\n{'Light' if light else 'Full'} refresh complete.")


if __name__ == "__main__":
    main(light="light" in sys.argv)
