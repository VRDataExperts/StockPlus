# StocksPlus — VM Setup (automation)

Goal: get the Droplet running the pipeline on a schedule (hourly + daily + weekend),
writing to Supabase so the Vercel dashboard stays current on its own.

Windows reminder: PC prompt = `raake@Rakesh`; VM prompt = `root@ubuntu-s-...` (after `ssh root@134.122.21.89`).

---

## 0. One-time prep in Supabase (Browser)
Make sure every table exists. In Supabase → SQL Editor, run each file's contents once
(skip any you've already run):
- `shared/schema.sql`
- `shared/schema_dashboard.sql`
- `shared/schema_opportunities.sql`
- `shared/schema_fundamentals.sql`
- `shared/schema_charts.sql`

If a table is missing, the full refresh will error when it tries to write to it.

## 1. Push latest code (PC)
```
cd /c/Users/raake/Desktop/StockPlus
git add . && git commit -m "latest" && git push
```

## 2. Copy your secrets to the VM (PC) — only if not done already
```
scp /c/Users/raake/Desktop/StockPlus/.env root@134.122.21.89:/home/trader/StockPlus/.env
```

## 3. On the VM — SSH in, then run everything below
```
ssh root@134.122.21.89
```

### 3a. Fix git ownership (one time) + pull latest + install deps
```
git config --global --add safe.directory /home/trader/StockPlus
cd /home/trader/StockPlus
git pull
.venv/bin/pip install -r engine/requirements.txt
ls -l .env            # must exist
```

### 3b. Set the clock to Eastern (one time)
```
timedatectl set-timezone America/New_York
date                  # confirm EST/EDT
```

### 3c. Make sure cron is installed and running
```
systemctl enable --now cron 2>/dev/null || (apt update && apt install -y cron && systemctl enable --now cron)
```

### 3d. Test the pipeline once (no waiting)
```
.venv/bin/python engine/refresh.py light     # quick: news + screener
.venv/bin/python engine/refresh.py           # full: fundamentals + backtests + charts + screener
```
Both should finish without tracebacks and print row counts.

### 3e. Install the cron jobs
```
( crontab -l 2>/dev/null | grep -v refresh.py; \
  echo "0 7-21 * * 1-5 cd /home/trader/StockPlus && .venv/bin/python engine/refresh.py light >> /home/trader/refresh.log 2>&1"; \
  echo "30 16 * * 1-5 cd /home/trader/StockPlus && .venv/bin/python engine/refresh.py >> /home/trader/refresh.log 2>&1"; \
  echo "0 9 * * 6 cd /home/trader/StockPlus && .venv/bin/python engine/refresh.py >> /home/trader/refresh.log 2>&1" \
) | crontab -
crontab -l            # confirm 3 lines
```

Schedule: light refresh hourly 7am–9pm ET (Mon–Fri), full refresh 4:30pm ET (Mon–Fri),
plus one full refresh Saturday 9am ET.

---

## Checking it's working
```
tail -f /home/trader/refresh.log     # watch the next scheduled run
```
Then open the Vercel dashboard — Opportunities, News, and Charts should reflect the latest run.

## When you change code later
1. PC: `git add . && git commit -m "..." && git push`
2. VM: `cd /home/trader/StockPlus && git pull`
(The cron picks up the new code automatically on its next run.)

## Common errors
- "dubious ownership" → run the `git config --global --add safe.directory ...` line (3a).
- "No such file ... refresh.py" → `git pull` didn't run; redo 3a.
- "Missing config: SUPABASE_URL ..." → `.env` missing on the VM; redo step 2.
- "relation ... does not exist" → a schema SQL file wasn't run in Supabase; redo step 0.
