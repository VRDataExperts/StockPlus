-- Volatile/low-price short-term movers. Run after schema.sql.
create table if not exists movers (
    id          bigint generated always as identity primary key,
    run_at      timestamptz not null default now(),
    as_of       date,
    ticker      text not null,
    horizon     text not null,        -- 'day' | 'week' | 'month'
    strategy    text not null,
    signal      text not null,        -- 'buy' | 'hold-long'
    confidence  numeric,              -- 0-100
    volatility  numeric,              -- annualized %
    momentum    numeric,              -- 20-day return
    sentiment   numeric,
    last_price  numeric,
    fresh       boolean default false
);
create index if not exists idx_movers_conf on movers (confidence desc);
alter table movers enable row level security;
drop policy if exists "public read movers" on movers;
create policy "public read movers" on movers for select using (true);
