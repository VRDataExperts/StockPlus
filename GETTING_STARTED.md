# StocksPlus — Getting Started (zero-knowledge walkthrough)

Follow these in order. Each step says **WHERE** to do it. Don't skip the WHERE — most mistakes come from running a command in the wrong window.

**Three "places" you'll use:**
- **Browser** — websites (IBKR, Supabase, GitHub, DigitalOcean).
- **Your PC terminal** — PowerShell on your computer. Prompt looks like `PS C:\Users\raake>`.
- **The Droplet** — your cloud server, reached over SSH. Prompt looks like `root@ubuntu-s-1vcpu-1gb-nyc1:~#`.

Nothing here uses real money. We connect to a **paper (fake-money) account** the whole way.

---

## PHASE 1 — Get an Interactive Brokers paper account  (Browser)

The engine has nothing to talk to without this. It's the gating step.

1. Go to **interactivebrokers.ca** → **Open Account**.
2. Choose **Individual** account and complete the application (ID, address, basic financial questions). Approval can take **a few hours to ~2 business days** — this is normal.
3. Once approved, log in to the **Client Portal** (the main IBKR website after login).
4. Open the menu → **Settings** → **Account Settings** → find **Paper Trading Account** → **Create**.
5. IBKR creates a **separate paper username and password** (different from your real login). **Write these down** — you'll type them into the server later.

> Faster option just to test: at **ibkr.com** you can sometimes register a **free trial / demo paper account** without a full application. It expires after a few weeks, but it's enough to prove the pipeline works. The proper paper account above is the long-term one.

When you have a **paper username + password**, continue.

---

## PHASE 2 — Create your database tables  (Browser → Supabase)

1. Open your project at **supabase.com**.
2. Left sidebar → **SQL Editor** → **New query**.
3. Open the file `shared/schema.sql` from your repo, copy **all** of it, paste into the editor.
4. Click **Run**. You should see "Success". This creates all your tables (strategies, orders, positions, news, etc.).

If you see an error, copy it to me.

---

## PHASE 3 — Prepare the server  (Droplet)

1. **On your PC terminal**, connect to the Droplet:
   ```
   ssh root@134.122.21.89
   ```
   If asked "Are you sure...", type `yes`. Your prompt should now read `root@ubuntu-s-...`.

2. **On the Droplet**, run the setup script (safe to run even if you ran it before):
   ```
   cd /root
   wget -O provision.sh https://raw.githubusercontent.com/VRDataExperts/StockPlus/main/engine/provision.sh
   bash provision.sh
   ```
   Wait for the **DONE** block at the end. This installs Java, IB Gateway, IBC, and the Python tools.

---

## PHASE 4 — Put in your IBKR paper login  (Droplet)

This is the only place your IBKR password goes. It stays on the server and is never sent anywhere.

1. **On the Droplet**, open the config file:
   ```
   nano /opt/ibc/config/config.ini
   ```
2. Find these two lines and replace the placeholders with your **paper** login from Phase 1:
   ```
   IbLoginId=YOUR_PAPER_USERNAME
   IbPassword=YOUR_PAPER_PASSWORD
   ```
3. Save and exit nano: press **Ctrl+O**, then **Enter**, then **Ctrl+X**.

---

## PHASE 5 — Start IB Gateway and keep it running  (Droplet)

We install it as a service so it auto-starts and restarts itself.

1. **On the Droplet**, install the service file and turn it on:
   ```
   cp /home/trader/StockPlus/engine/ibgateway.service /etc/systemd/system/
   systemctl daemon-reload
   systemctl enable --now ibgateway
   ```
2. Give it ~30 seconds, then check it's alive:
   ```
   systemctl status ibgateway --no-pager
   ```
   You want to see **active (running)**. (Press `q` to exit the status view.)

---

## PHASE 6 — Test the connection  (Droplet)

This reads your paper account. It places **no trades**.

```
cd /home/trader/StockPlus
. .venv/bin/activate
python engine/test_connection.py
```

Success looks like:
```
Connected.
Account summary:
  NetLiquidation   1000000 USD
  ...
All good — engine can talk to your paper account.
```

If you see that, the hard part is done — the server can read your IBKR paper account, and we're ready to build strategies.

---

## If something fails
Copy the exact error text and send it to me. The usual culprits:
- **Connection refused / timeout** in Phase 6 → IB Gateway isn't up yet; wait a minute, recheck `systemctl status ibgateway`.
- **Login failed** → wrong paper username/password in `config.ini`, or you used the live login instead of the paper one.
- **wget / file not found** → you're on your PC, not the Droplet. Re-run `ssh root@134.122.21.89` first.

---

## What's next (after Phase 6 passes)
1. I build the **first strategy** (technical/momentum) — reads prices, writes signals to Supabase, places **paper** orders only.
2. We add **risk controls** (max daily loss, max position, kill switch).
3. We add the **news feed** (Finnhub/MT Newswires) and the **dashboard** on Vercel.
4. Weeks of paper validation → only then, tiny real capital.
