-- Near-real-time quotes for the live price strip. Run after schema.sql.
create table if not exists live_quotes (
    ticker      text primary key,
    price       numeric,
    prev_close  numeric,
    change_pct  numeric,
    updated_at  timestamptz not null default now()
);
alter table live_quotes enable row level security;
drop policy if exists "public read live" on live_quotes;
create policy "public read live" on live_quotes for select using (true);
