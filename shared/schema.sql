-- StocksPlus database schema
-- Paste this into Supabase: Dashboard -> SQL Editor -> New query -> Run
-- Safe to re-run: uses IF NOT EXISTS.

-- ============================================================
-- STRATEGIES: configs + on/off switches
-- ============================================================
create table if not exists strategies (
    id           bigint generated always as identity primary key,
    name         text not null unique,
    style        text not null check (style in ('momentum','news','etf_rebalance')),
    params       jsonb not null default '{}'::jsonb,   -- thresholds, indicators, etc.
    enabled      boolean not null default false,
    created_at   timestamptz not null default now(),
    updated_at   timestamptz not null default now()
);

-- ============================================================
-- SIGNALS: buy/sell intents produced by a strategy
-- ============================================================
create table if not exists signals (
    id           bigint generated always as identity primary key,
    strategy_id  bigint references strategies(id),
    source       text not null,                         -- 'engine' | 'tradingview' | 'manual'
    ticker       text not null,
    exchange     text,                                  -- 'SMART','TSE','NYSE',...
    side         text not null check (side in ('buy','sell')),
    qty          numeric,
    reason       text,                                  -- why it fired
    created_at   timestamptz not null default now(),
    processed    boolean not null default false
);

-- ============================================================
-- ORDERS: every order sent to the broker + its result
-- ============================================================
create table if not exists orders (
    id              bigint generated always as identity primary key,
    signal_id       bigint references signals(id),
    broker          text not null default 'ibkr',
    account         text,                               -- paper or live account id
    ticker          text not null,
    side            text not null check (side in ('buy','sell')),
    qty             numeric not null,
    order_type      text not null default 'MKT',        -- MKT, LMT, ...
    limit_price     numeric,
    status          text not null default 'submitted',  -- submitted/filled/cancelled/rejected
    filled_qty      numeric default 0,
    avg_fill_price  numeric,
    broker_order_id text,
    is_paper        boolean not null default true,
    created_at      timestamptz not null default now(),
    updated_at      timestamptz not null default now()
);

-- ============================================================
-- POSITIONS: periodic snapshots of holdings
-- ============================================================
create table if not exists positions (
    id            bigint generated always as identity primary key,
    account       text,
    ticker        text not null,
    qty           numeric not null,
    avg_cost      numeric,
    market_price  numeric,
    market_value  numeric,
    unrealized_pnl numeric,
    is_paper      boolean not null default true,
    snapshot_at   timestamptz not null default now()
);

-- ============================================================
-- NEWS_ITEMS: ingested headlines + sentiment
-- ============================================================
create table if not exists news_items (
    id           bigint generated always as identity primary key,
    provider     text not null,                         -- 'finnhub','mtnewswires',...
    headline     text not null,
    url          text,
    tickers      text[],
    sentiment    numeric,                               -- -1..1 if available
    published_at timestamptz,
    ingested_at  timestamptz not null default now(),
    external_id  text,
    unique (provider, external_id)
);

-- ============================================================
-- RISK_STATE: one row per trading day; the safety layer
-- ============================================================
create table if not exists risk_state (
    trade_date        date primary key,
    realized_pnl      numeric not null default 0,
    open_positions    int not null default 0,
    max_daily_loss    numeric not null default 0,        -- limit; engine halts if breached
    max_position_size numeric not null default 0,
    kill_switch       boolean not null default false,    -- true = stop all trading
    updated_at        timestamptz not null default now()
);

-- ============================================================
-- AUDIT_LOG: append-only record of every action
-- ============================================================
create table if not exists audit_log (
    id          bigint generated always as identity primary key,
    actor       text not null,                          -- 'engine','dashboard','cron'
    action      text not null,
    detail      jsonb,
    created_at  timestamptz not null default now()
);

-- ============================================================
-- Enable Row Level Security (lock down by default).
-- The engine/dashboard use the service_role key which bypasses RLS.
-- Add granular policies later if you expose anon/user access.
-- ============================================================
alter table strategies  enable row level security;
alter table signals     enable row level security;
alter table orders      enable row level security;
alter table positions   enable row level security;
alter table news_items  enable row level security;
alter table risk_state  enable row level security;
alter table audit_log   enable row level security;

-- Helpful indexes
create index if not exists idx_signals_unprocessed on signals (processed, created_at);
create index if not exists idx_orders_status on orders (status, created_at);
create index if not exists idx_news_published on news_items (published_at desc);
create index if not exists idx_positions_snapshot on positions (snapshot_at desc);
