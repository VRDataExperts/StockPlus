-- Opportunities table for the daily screener. Run after schema.sql.
create table if not exists opportunities (
    id          bigint generated always as identity primary key,
    run_at      timestamptz not null default now(),
    as_of       date,
    ticker      text not null,
    strategy    text not null,
    signal      text not null,        -- 'buy' (fresh entry) or 'hold-long'
    last_price  numeric,
    score       numeric,              -- 20-day trailing return, for ranking
    fresh       boolean default false
);
create index if not exists idx_opps_score on opportunities (score desc);

alter table opportunities enable row level security;
drop policy if exists "public read opps" on opportunities;
create policy "public read opps" on opportunities for select using (true);
