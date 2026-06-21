-- Fundamentals + company-strength score. Run after schema.sql / schema_opportunities.sql.
create table if not exists fundamentals (
    ticker          text primary key,
    name            text,
    sector          text,
    market_cap      numeric,
    pe              numeric,
    profit_margin   numeric,
    roe             numeric,
    revenue_growth  numeric,
    debt_to_equity  numeric,
    gross_margin    numeric,
    strength_score  numeric,
    updated_at      timestamptz not null default now()
);
alter table fundamentals enable row level security;
drop policy if exists "public read fundamentals" on fundamentals;
create policy "public read fundamentals" on fundamentals for select using (true);

-- enrich opportunities with strength + sentiment
alter table opportunities add column if not exists strength_score numeric;
alter table opportunities add column if not exists sentiment numeric;
