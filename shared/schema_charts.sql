-- Per-ticker chart data for the Charts page. Run after schema.sql.
create table if not exists chart_data (
    ticker     text primary key,
    points     jsonb not null,   -- [{t, close, sma20, sma50, bb_up, bb_lo}, ...]
    markers    jsonb not null,   -- [{t, side, strategy, price}, ...]
    updated_at timestamptz not null default now()
);
alter table chart_data enable row level security;
drop policy if exists "public read charts" on chart_data;
create policy "public read charts" on chart_data for select using (true);
