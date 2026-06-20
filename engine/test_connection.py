"""
StocksPlus — IBKR connection test.

Confirms the engine can reach IB Gateway (paper) and read the account.
It only READS. It places no orders.

Run on the VM after provision.sh and after IB Gateway is started:
    cd /home/trader/StockPlus && . .venv/bin/activate
    python engine/test_connection.py

Uses ib_async (the maintained successor to ib_insync; same API).
"""

from ib_async import IB, util

# IB Gateway default API ports:  paper = 4002, live = 4001
HOST = "127.0.0.1"
PORT = 4002          # paper
CLIENT_ID = 1        # any unique integer


def main() -> None:
    ib = IB()
    print(f"Connecting to IB Gateway at {HOST}:{PORT} (paper)...")
    try:
        ib.connect(HOST, PORT, clientId=CLIENT_ID, timeout=15)
    except Exception as e:
        print(f"  CONNECTION FAILED: {e}")
        print("  Checks: is IB Gateway running? Is TradingMode=paper? Port 4002 open locally?")
        return

    print("  Connected.\n")

    # Account summary
    print("Account summary:")
    for row in ib.accountSummary():
        if row.tag in ("NetLiquidation", "TotalCashValue", "BuyingPower", "AvailableFunds"):
            print(f"  {row.tag:18} {row.value} {row.currency}")

    # Current positions
    positions = ib.positions()
    print(f"\nOpen positions: {len(positions)}")
    for p in positions:
        print(f"  {p.contract.symbol:8} qty={p.position} avgCost={p.avgCost}")

    # Quick market-data sanity check (delayed data is fine for the test)
    from ib_async import Stock
    ib.reqMarketDataType(3)  # 3 = delayed
    spy = Stock("SPY", "SMART", "USD")
    ib.qualifyContracts(spy)
    ticker = ib.reqMktData(spy)
    ib.sleep(2)
    print(f"\nSPY last/close: {ticker.last or ticker.close}")

    ib.disconnect()
    print("\nAll good — engine can talk to your paper account.")


if __name__ == "__main__":
    util.startLoop()  # harmless in scripts; helps in notebooks
    main()
