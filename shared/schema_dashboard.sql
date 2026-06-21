-- StocksPlus dashboard tables. Run AFTER schema.sql.
-- Stores backtest results + equity curves, and exposes read-only access
-- to the public dashboard via RLS (the anon key can SELECT, never write).

create table if not exists backtests (
    id              bigint generated always as identity primary key,
    run_at          timestamptz not null default now(),
    strategy        text not null,
    ticker          text not null,
    period_label    text not null,
    total_return        numeric,
    cagr                numeric,
    max_drawdown        numeric,
    sharpe              numeric,
    bh_total_return     numeric,
    bh_max_drawdown     numeric,
    bh_sharpe           numeric,
    trades              int,
    time_in_market      numeric
);

create table if not exists backtest_curves (
    backtest_id  bigint primary key references backtests(id) on delete cascade,
    points       jsonb not null   -- [{t, strat, bh}, ...] downsampled equity curves
);

create index if not exists idx_backtests_run on backtests (run_at desc);
create index if not exists idx_backtests_lookup on backtests (strategy, ticker, period_label);

-- ---- Read-only public access for the dashboard (anon key) ----
alter table backtests       enable row level security;
alter table backtest_curves enable row level security;

drop policy if exists "public read backtests" on backtests;
create policy "public read backtests" on backtests for select using (true);

drop policy if exists "public read curves" on backtest_curves;
create policy "public read curves" on backtest_curves for select using (true);

-- Let the dashboard show recent news too
drop policy if exists "public read news" on news_items;
create policy "public read news" on news_items for select using (true);
