# StocksPlus Dashboard — deploy to Vercel

A visual dashboard for your strategy backtests and market news. The heavy
compute runs on your machine and writes results to Supabase; this page just
reads Supabase and draws charts. No command line needed once it's live.

## One-time data setup

**1. Add the dashboard tables** (Browser → Supabase → SQL Editor → New query):
Paste `shared/schema_dashboard.sql`, Run. This adds `backtests` + `backtest_curves`
and read-only public access for the dashboard.

**2. Populate results** (PC terminal, in the project folder):
First make sure your `.env` has Supabase keys (see below), then:
```
python engine/compare.py
```
This runs all three strategies across the basket and the 2022 bear window, and
writes everything to Supabase. Re-run anytime to refresh — newest results win.

For the News tab:
```
python engine/news_ingest.py
```

## Wire the dashboard to Supabase

Open `dashboard/index.html` and fill in the two values near the bottom
(Supabase → **Project Settings → API**):
```js
const SUPABASE_URL = 'https://YOUR-PROJECT.supabase.co';
const SUPABASE_ANON_KEY = 'your-anon-public-key';
```
Use the **anon / public** key here — NOT the service_role key. The anon key is
designed to be public and Row Level Security limits it to reads. Commit and push.

## Deploy on Vercel

1. Go to **vercel.com → Add New → Project** → import `VRDataExperts/StockPlus`.
2. **Root Directory:** set to `dashboard`.
3. **Framework Preset:** Other (it's a static site — no build step).
4. Click **Deploy**. In ~30s you get a live URL like `stockplus.vercel.app`.

That's it — open the URL and you'll see the backtest table, click any row for its
equity curve, and switch to the News tab for headlines. Re-running `compare.py`
or `news_ingest.py` and hitting **Refresh** updates the page.

## .env reference (PC, never committed)
```
SUPABASE_URL=https://YOUR-PROJECT.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key   # used by compare.py / news_ingest.py
FINNHUB_API_KEY=your-finnhub-key
```
Note: `compare.py` and `news_ingest.py` use the **service_role** key (full write).
The dashboard uses the **anon** key (read only). Keep them straight.

## Troubleshooting
- **Dashboard shows a yellow warning bar** → you didn't fill the URL/anon key in index.html.
- **Empty table** → run `python engine/compare.py` (and check it printed "Wrote N backtests").
- **Empty news** → run `python engine/news_ingest.py`.
- **Browser console 401/permission errors** → re-run `schema_dashboard.sql` (the public read policies didn't apply).
