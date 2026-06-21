"""
Full daily refresh: fundamentals -> news -> backtests -> screener.
Run on an always-on machine (the VM) via cron. One failure won't stop the rest.

    python engine/refresh.py
"""
from __future__ import annotations
import traceback


def _step(name, fn):
    print(f"\n===== {name} =====")
    try:
        fn()
    except Exception:
        print(f"[{name}] FAILED:")
        traceback.print_exc()


def main():
    import fundamentals, news_ingest, compare, screen
    _step("fundamentals", lambda: fundamentals.main(dry=False))
    _step("news", lambda: news_ingest.main())
    _step("backtests", lambda: compare.main(dry=False))
    _step("screener", lambda: screen.main(dry=False))
    print("\nRefresh complete.")


if __name__ == "__main__":
    main()
