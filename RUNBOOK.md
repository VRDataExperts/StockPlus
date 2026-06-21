# StocksPlus — Complete Runbook + Claude Code prompt

Two parts:
- **Part A** — every step, in order, to go from the current repo to a live visual dashboard on Vercel.
- **Part B** — a prompt you can paste into Claude Code to automate the parts a coding agent can do.

Windows reminder:
- **PC terminal** prompt = `raake@Rakesh` / `PS C:\Users\raake>` (your computer).
- **Droplet** = only after `ssh root@134.122.21.89` (the cloud server; needed later for live trading, NOT for the dashboard).

---

## PART A — Step by step

### 1. Push the latest code  (PC, project folder)
```
cd C:\Users\raake\Desktop\StockPlus
git add .
git commit -m "strategies, compare engine, dashboard, runbook"
git push
```

### 2. Install Python libraries  (PC)
```
python -m pip install -r engine/requirements.txt
```

### 3. Create the database tables  (Browser → Supabase)
- Supabase → your project → **SQL Editor → New query**.
- Paste all of `shared/schema.sql` → **Run**.
- New query again → paste all of `shared/schema_dashboard.sql` → **Run**.

### 4. Make your secrets file  (PC, project folder)
- Copy the template: in File Explorer copy `.env.example` to `.env` (or `copy .env.example .env`).
- Open `.env` in Notepad and fill in:
  - `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` → Supabase → **Project Settings → API**.
  - `FINNHUB_API_KEY` → your Finnhub key.
- Save. (`.env` is gitignored — it will never be pushed.)

### 5. Generate the data  (PC)
```
python engine/compare.py
python engine/news_ingest.py
```
`compare.py` should end with "Wrote N backtests to Supabase". `news_ingest.py` reports how many headlines it stored.

### 6. Connect the dashboard to Supabase  (PC, edit file)
- Open `dashboard/index.html`, find the two lines near the bottom:
  ```
  const SUPABASE_URL = 'YOUR_SUPABASE_URL';
  const SUPABASE_ANON_KEY = 'YOUR_SUPABASE_ANON_KEY';
  ```
- Replace with your Project URL and the **anon / public** key (Supabase → Project Settings → API). NOT the service_role key.
- Save, then:
```
git add . && git commit -m "wire dashboard to supabase" && git push
```

### 7. Deploy the dashboard  (Browser → Vercel)
- vercel.com → **Add New → Project** → import `VRDataExperts/StockPlus`.
- **Root Directory:** `dashboard`
- **Framework Preset:** Other (no build step).
- **Deploy.** You get a live URL in ~30 seconds.

### 8. Use it
- Open the Vercel URL. Backtests tab: sort columns, click any row to chart strategy vs buy & hold. News tab: latest headlines.
- To refresh data later: re-run step 5, then click **Refresh** on the page.

### Later (after IBKR paper approval) — live engine
- On the **Droplet**: edit `/opt/ibc/config/config.ini` with your IBKR paper login, start the `ibgateway` service, run `python engine/test_connection.py`. See `GETTING_STARTED.md` phases 4–6. We add order placement only after weeks of paper validation.

---

## PART B — Claude Code prompt

Claude Code (the terminal coding agent) can do the file/code/run/deploy steps. It
**cannot** open your IBKR/Supabase/Vercel accounts, type secrets it doesn't have, or
place trades. Provide your keys when it asks. Run Claude Code from the project folder
(`C:\Users\raake\Desktop\StockPlus`) and paste the prompt below.

```
You are working in my StocksPlus repo (a paper-trading research project). The code
is already written: engine/ has config.py, db.py, news_ingest.py, compare.py,
metrics.py, backtest.py and strategies/ (momentum, breakout, mean_reversion);
shared/ has schema.sql and schema_dashboard.sql; dashboard/index.html is a static
Supabase-backed dashboard. Goal: get the visual dashboard live on Vercel with real
backtest + news data. Do these steps, pausing to ask me for any secret you need:

1. Verify the repo structure and run: python -m pip install -r engine/requirements.txt
2. Confirm a .env exists in the project root. If not, create it from .env.example and
   ask me for SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, and FINNHUB_API_KEY. Never
   commit .env (check .gitignore already excludes it).
3. The Supabase tables come from shared/schema.sql then shared/schema_dashboard.sql.
   If I give you the Supabase DB connection string, run them with psql; otherwise
   tell me to paste both files into the Supabase SQL Editor and wait for my confirmation.
4. Run: python engine/compare.py  and  python engine/news_ingest.py
   Report the row counts they print. If they error, diagnose and fix.
5. In dashboard/index.html replace SUPABASE_URL and SUPABASE_ANON_KEY placeholders
   with the values I provide (anon/public key, not service_role).
6. git add/commit/push the changes (but never the .env).
7. If the Vercel CLI is installed and I'm logged in, deploy the dashboard/ folder
   (root directory = dashboard, static, no build). Otherwise give me the exact
   vercel.com import steps.

Constraints: this is paper/research only — do not write any code that places live
trades or moves money. Keep secrets out of git. Ask before destructive actions.
```

Notes:
- If Claude Code doesn't have the `vercel` CLI or Supabase connection string, it will hand those one or two steps back to you — that's expected.
- It will need you to paste the three keys at step 2 and the anon key at step 5.
